package cn.iocoder.yudao.module.cafe.service.order;
import cn.hutool.crypto.digest.DigestUtil;
import cn.iocoder.yudao.module.cafe.controller.app.order.vo.OrderCreateReqVO;
import cn.iocoder.yudao.module.cafe.dal.dataobject.*;
import cn.iocoder.yudao.module.cafe.dal.mysql.*;
import cn.iocoder.yudao.module.cafe.framework.CafeProperties;
import cn.iocoder.yudao.module.cafe.service.menu.MenuService;
import cn.iocoder.yudao.module.cafe.service.shop.ShopService;
import cn.iocoder.yudao.module.cafe.service.card.StudentCardClient;
import cn.iocoder.yudao.module.cafe.enums.OrderStatusEnum;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;
import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.*;
/** 数据库事务只保存本地数据；学生卡请求始终在事务提交之后。 */
@Service @Slf4j public class OrderServiceImpl implements OrderService {
    @Resource private OrderMapper orders;
    @Resource private OrderItemMapper orderItems;
    @Resource private StudentMapper students;
    @Resource private MenuService menu;
    @Resource private ShopService shop;
    @Resource private StudentCardClient cards;
    @Resource private CafeProperties properties;
    @Resource private Clock cafeClock;
    @Resource private TransactionTemplate transactions;
    private record Draft(OrderDO order,boolean fresh) {}
    public Long create(Long studentId,OrderCreateReqVO request,String idempotencyKey){
        if(idempotencyKey!=null&&(idempotencyKey.isBlank()||idempotencyKey.length()>64))throw new IllegalArgumentException("重复请求标识应为 1–64 个字符");
        String fingerprint=fingerprint(request);
        Draft draft=Objects.requireNonNull(transactions.execute(tx->{
            // 同一学生串行创建草稿，保护无幂等标识时的短时间重复点击。
            StudentDO student=students.lockById(studentId);if(student==null)throw exception(STUDENT_NOT_FOUND);
            OrderDO existing;
            if(idempotencyKey!=null){
                existing=orders.selectOne(new LambdaQueryWrapper<OrderDO>().eq(OrderDO::getStudentId,studentId).eq(OrderDO::getRequestKey,idempotencyKey));
            } else {
                existing=orders.selectOne(new LambdaQueryWrapper<OrderDO>().eq(OrderDO::getStudentId,studentId).eq(OrderDO::getFingerprint,fingerprint)
                    .ge(OrderDO::getCreateTime,now().minusSeconds(3)).orderByDesc(OrderDO::getId).last("LIMIT 1"));
            }
            if(existing!=null){if(!existing.getFingerprint().equals(fingerprint))throw exception(REQUEST_CONFLICT);return new Draft(existing,false);}
            // A student may have another timed-out or compensating payment. Do not
            // let a new key turn that unresolved attempt into a second debit.
            if(orders.selectCount(new LambdaQueryWrapper<OrderDO>().eq(OrderDO::getStudentId,studentId)
                .in(OrderDO::getStatus,0,2))>0)throw exception(ORDER_PAYING);
            if(!shop.canOrder())throw exception(SHOP_CLOSED);
            var quote=OrderPricing.calculate(request,menu.getMenu(true).getItems(),properties.getOrder().getMaxCups());
            OrderDO order=new OrderDO();order.setStudentId(studentId);order.setStudentNo(student.getStudentNo());order.setStudentName(student.getName());
            order.setOrderNo("C"+now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"))+UUID.randomUUID().toString().replace("-","").substring(0,12));
            order.setStatus(0);order.setBusinessDate(today());order.setTotalPrice(quote.totalPrice());order.setCupCount(quote.cupCount());
            order.setRequestKey(idempotencyKey==null?"auto:"+UUID.randomUUID():idempotencyKey);order.setFingerprint(fingerprint);order.setVersion(0);order.setCreateTime(now());
            orders.insert(order);
            quote.items().forEach(item->{item.setOrderId(order.getId());orderItems.insert(item);});
            return new Draft(order,true);
        }));
        OrderDO order=draft.order();
        if(!draft.fresh())return replay(order);
        StudentCardClient.DebitResult result;
        try {result=cards.debit(order.getStudentNo(),order.getTotalPrice(),order.getOrderNo());}
        catch(Exception ex){log.warn("学生卡扣款结果不明，App 订单 {}",order.getOrderNo());result=StudentCardClient.DebitResult.UNKNOWN;}
        if(result==StudentCardClient.DebitResult.SUCCESS){
            if(orders.changePayment(order.getId(),0,order.getVersion(),10,null,null,now())==1)return order.getId();
            // 慢请求可能已被恢复任务接管。绝不把已冲正的订单再改成待录单。
            throw exception(PAYMENT_UNKNOWN);
        }
        if(result==StudentCardClient.DebitResult.DECLINED){
            if(orders.changePayment(order.getId(),0,order.getVersion(),1,"学生卡明确拒绝扣款",null,now())==1)throw exception(CARD_DECLINED);
            throw exception(PAYMENT_UNKNOWN);
        }
        if(orders.changePayment(order.getId(),0,order.getVersion(),2,"扣款结果不明",now(),now())==1){
            order.setStatus(2);order.setVersion(order.getVersion()+1);compensate(order);
        }
        throw exception(PAYMENT_UNKNOWN);
    }
    private Long replay(OrderDO order){
        if(OrderStatusEnum.visible(order.getStatus()))return order.getId();
        if(order.getStatus()==1){
            if("学生卡明确拒绝扣款".equals(order.getFailureReason()))throw exception(CARD_DECLINED);
            if("扣款结果不明，已执行补偿，请稍后查看余额".equals(order.getFailureReason()))throw exception(ORDER_REFUNDED);
            throw exception(PAYMENT_UNKNOWN);
        }
        throw exception(ORDER_PAYING);
    }
    @Scheduled(fixedDelayString="${cafe.order.recovery-delay-ms:60000}",initialDelayString="${cafe.order.recovery-delay-ms:60000}")
    public void recoverPayments(){
        LocalDateTime cutoff=now().minusSeconds(properties.getOrder().getPaymentTimeoutSeconds());
        var stale=orders.selectList(new LambdaQueryWrapper<OrderDO>().eq(OrderDO::getStatus,0).le(OrderDO::getCreateTime,cutoff).orderByAsc(OrderDO::getId).last("LIMIT 100"));
        for(var order:stale){
            if(orders.changePayment(order.getId(),0,order.getVersion(),2,"支付中断，自动补偿",now(),now())==1){order.setVersion(order.getVersion()+1);order.setStatus(2);compensate(order);}
        }
        var retry=orders.selectList(new LambdaQueryWrapper<OrderDO>().eq(OrderDO::getStatus,2).le(OrderDO::getRetryAfter,now()).orderByAsc(OrderDO::getId).last("LIMIT 100"));
        for(var order:retry)compensate(order);
    }
    private void compensate(OrderDO order){
        // 租约及版本号避免多节点重复领取；退款边界另以 orderNo 幂等。
        LocalDateTime retryAfter=now().plusSeconds(60);
        if(orders.changePayment(order.getId(),2,order.getVersion(),2,order.getFailureReason(),retryAfter,now())!=1)return;
        int claimedVersion=order.getVersion()+1;
        try {
            cards.refund(order.getStudentNo(),order.getTotalPrice(),order.getOrderNo());
            orders.changePayment(order.getId(),2,claimedVersion,1,"扣款结果不明，已执行补偿，请稍后查看余额",null,now());
        } catch(Exception ex){
            log.error("学生卡补偿失败，将重试，App 订单 {}",order.getOrderNo());
            orders.changePayment(order.getId(),2,claimedVersion,2,"补偿尚未确认，系统将自动重试",retryAfter,now());
        }
    }
    public void enter(Long id,String posOrderNo){
        String pos=posOrderNo==null?"":posOrderNo.trim();if(pos.isBlank()||pos.length()>20)throw new IllegalArgumentException("收银单号不能为空，最长 20 个字符");
        OrderDO order=getToday(id);if(order.getStatus()!=10&&order.getStatus()!=20)throw exception(ORDER_CHANGED);
        try {if(orders.enter(id,order.getStatus(),order.getVersion(),pos,now())!=1)throw exception(ORDER_CHANGED);}
        catch(DuplicateKeyException ex){throw exception(POS_DUPLICATE);}
    }
    public void done(Long id){OrderDO order=getToday(id);if(order.getStatus()!=20||orders.changeState(id,20,order.getVersion(),30,now(),now())!=1)throw exception(ORDER_CHANGED);}
    public void undoDone(Long id){OrderDO order=getToday(id);if(order.getStatus()!=30||orders.changeState(id,30,order.getVersion(),20,null,now())!=1)throw exception(ORDER_CHANGED);}
    private OrderDO getToday(Long id){OrderDO order=orders.selectById(id);if(order==null)throw exception(ORDER_NOT_FOUND);if(!today().equals(order.getBusinessDate()))throw exception(ORDER_NOT_TODAY);return order;}
    private LocalDateTime now(){return LocalDateTime.now(cafeClock);}
    private LocalDate today(){return LocalDate.now(cafeClock);}
    private String fingerprint(OrderCreateReqVO request){
        String canonical=request.getItems().stream().map(item->item.getItemId()+":"+item.getQuantity()+":"+item.getOptionIds().stream().sorted().map(String::valueOf).collect(Collectors.joining(",")))
            .sorted().collect(Collectors.joining(";"));return DigestUtil.sha256Hex(canonical);
    }
}
