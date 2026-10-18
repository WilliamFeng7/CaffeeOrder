package cn.iocoder.yudao.module.cafe.service.order;
import cn.iocoder.yudao.framework.common.pojo.*;
import cn.iocoder.yudao.framework.common.util.object.BeanUtils;
import cn.iocoder.yudao.module.cafe.controller.app.order.vo.OrderRespVO;
import cn.iocoder.yudao.module.cafe.controller.admin.order.vo.*;
import cn.iocoder.yudao.module.cafe.controller.admin.barista.vo.BaristaOrderRespVO;
import cn.iocoder.yudao.module.cafe.dal.dataobject.*;
import cn.iocoder.yudao.module.cafe.dal.mysql.*;
import cn.iocoder.yudao.module.cafe.enums.OrderStatusEnum;
import com.baomidou.mybatisplus.core.conditions.query.*;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;
import java.time.*;
import java.util.*;
import java.util.stream.Collectors;
import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.*;
@Service public class OrderQueryServiceImpl implements OrderQueryService {
    @Resource private OrderMapper orders;
    @Resource private OrderItemMapper items;
    @Resource private Clock cafeClock;
    public OrderRespVO getStudentOrder(Long studentId,Long orderId){
        OrderDO order=orders.selectById(orderId);if(order==null||!order.getStudentId().equals(studentId)||!OrderStatusEnum.visible(order.getStatus()))throw exception(ORDER_NOT_FOUND);
        return studentVOs(List.of(order)).get(0);
    }
    public PageResult<OrderRespVO> studentPage(Long studentId,PageParam page){
        var rows=orders.selectPage(page,new LambdaQueryWrapper<OrderDO>().eq(OrderDO::getStudentId,studentId).in(OrderDO::getStatus,10,20,30).orderByDesc(OrderDO::getCreateTime,OrderDO::getId));
        return new PageResult<>(studentVOs(rows.getList()),rows.getTotal());
    }
    public long waitingCount(){return orders.selectCount(activeToday());}
    private LambdaQueryWrapper<OrderDO> activeToday(){return new LambdaQueryWrapper<OrderDO>().eq(OrderDO::getBusinessDate,today()).in(OrderDO::getStatus,10,20);}
    private List<OrderRespVO> studentVOs(List<OrderDO> rows){
        var snapshots=snapshots(rows);var active=orders.selectList(activeToday().orderByAsc(OrderDO::getCreateTime,OrderDO::getId));
        Map<Long,Integer> ahead=new HashMap<>();for(int i=0;i<active.size();i++)ahead.put(active.get(i).getId(),i);
        return rows.stream().map(row->{var vo=BeanUtils.toBean(row,OrderRespVO.class);vo.setItems(BeanUtils.toBean(snapshots.getOrDefault(row.getId(),List.of()),OrderRespVO.Item.class));vo.setAheadCount(ahead.get(row.getId()));return vo;}).toList();
    }
    private Map<Long,List<OrderItemDO>> snapshots(List<OrderDO> rows){
        if(rows.isEmpty())return Map.of();
        return items.selectList(new LambdaQueryWrapper<OrderItemDO>().in(OrderItemDO::getOrderId,rows.stream().map(OrderDO::getId).toList()).orderByAsc(OrderItemDO::getId))
            .stream().collect(Collectors.groupingBy(OrderItemDO::getOrderId));
    }
    public Map<String,List<BaristaOrderRespVO>> board(){
        List<OrderDO> rows=orders.selectList(new LambdaQueryWrapper<OrderDO>().eq(OrderDO::getBusinessDate,today()).in(OrderDO::getStatus,10,20,30).orderByAsc(OrderDO::getCreateTime,OrderDO::getId));
        var snapshots=snapshots(rows);
        Map<Long,BaristaOrderRespVO> byId=new HashMap<>();
        for(var row:rows){var vo=BeanUtils.toBean(row,BaristaOrderRespVO.class);vo.setItems(BeanUtils.toBean(snapshots.getOrDefault(row.getId(),List.of()),BaristaOrderRespVO.Item.class));byId.put(row.getId(),vo);}
        return Map.of("waiting",rows.stream().filter(r->r.getStatus()==10).map(r->byId.get(r.getId())).toList(),
            "making",rows.stream().filter(r->r.getStatus()==20).map(r->byId.get(r.getId())).toList(),
            "recentDone",rows.stream().filter(r->r.getStatus()==30).sorted(Comparator.comparing(OrderDO::getDoneTime).thenComparing(OrderDO::getId).reversed()).limit(10).map(r->byId.get(r.getId())).toList());
    }
    public PageResult<AdminOrderRespVO> adminPage(OrderPageReqVO page){
        var rows=orders.selectPage(page,filter(page).orderByDesc(OrderDO::getCreateTime,OrderDO::getId));
        var snapshots=snapshots(rows.getList());
        var vos=rows.getList().stream().map(row->{var vo=BeanUtils.toBean(row,AdminOrderRespVO.class);vo.setItems(BeanUtils.toBean(snapshots.getOrDefault(row.getId(),List.of()),OrderRespVO.Item.class));return vo;}).toList();
        return new PageResult<>(vos,rows.getTotal());
    }
    public AdminOrderRespVO adminDetail(Long id){
        OrderDO row=orders.selectById(id);if(row==null)throw exception(ORDER_NOT_FOUND);
        var vo=BeanUtils.toBean(row,AdminOrderRespVO.class);vo.setItems(BeanUtils.toBean(snapshots(List.of(row)).getOrDefault(id,List.of()),OrderRespVO.Item.class));return vo;
    }
    public Map<String,Long> statistics(OrderPageReqVO page){
        // 三个统计值使用完全相同的筛选；失败/补偿中的订单不计入已扣款金额。
        QueryWrapper<OrderDO> query=new QueryWrapper<>();
        var wrapper=filter(page);
        query.select("COUNT(*) AS order_count","COALESCE(SUM(total_price),0) AS total_price","COALESCE(SUM(CASE WHEN status IN (10,20,30) THEN total_price ELSE 0 END),0) AS paid_amount");
        query.ge(page.getStartDate()!=null,"business_date",page.getStartDate()).le(page.getEndDate()!=null,"business_date",page.getEndDate()).eq(page.getStatus()!=null,"status",page.getStatus());
        if(page.getStudent()!=null&&!page.getStudent().isBlank())query.and(q->q.like("student_no",page.getStudent()).or().like("student_name",page.getStudent()));
        if(page.getPosOrderNo()!=null&&!page.getPosOrderNo().isBlank())query.eq("pos_order_no",page.getPosOrderNo().trim());
        var row=orders.selectMaps(query).get(0);
        return Map.of("orderCount",number(row,"order_count"),"totalPrice",number(row,"total_price"),"paidAmount",number(row,"paid_amount"));
    }
    private long number(Map<String,Object> row,String key){return ((Number)row.get(key)).longValue();}
    private LambdaQueryWrapper<OrderDO> filter(OrderPageReqVO page){
        var query=new LambdaQueryWrapper<OrderDO>().ge(page.getStartDate()!=null,OrderDO::getBusinessDate,page.getStartDate()).le(page.getEndDate()!=null,OrderDO::getBusinessDate,page.getEndDate()).eq(page.getStatus()!=null,OrderDO::getStatus,page.getStatus());
        if(page.getStudent()!=null&&!page.getStudent().isBlank())query.and(q->q.like(OrderDO::getStudentNo,page.getStudent()).or().like(OrderDO::getStudentName,page.getStudent()));
        if(page.getPosOrderNo()!=null&&!page.getPosOrderNo().isBlank())query.eq(OrderDO::getPosOrderNo,page.getPosOrderNo().trim());
        return query;
    }
    private LocalDate today(){return LocalDate.now(cafeClock);}
}
