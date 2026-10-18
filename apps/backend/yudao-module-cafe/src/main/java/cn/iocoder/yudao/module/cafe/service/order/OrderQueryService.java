package cn.iocoder.yudao.module.cafe.service.order;
import cn.iocoder.yudao.framework.common.pojo.*;
import cn.iocoder.yudao.module.cafe.controller.app.order.vo.OrderRespVO;
import cn.iocoder.yudao.module.cafe.controller.admin.order.vo.*;
import cn.iocoder.yudao.module.cafe.controller.admin.barista.vo.BaristaOrderRespVO;
import java.util.*;
public interface OrderQueryService {
    OrderRespVO getStudentOrder(Long studentId,Long orderId);
    PageResult<OrderRespVO> studentPage(Long studentId,PageParam page);
    long waitingCount();
    Map<String,List<BaristaOrderRespVO>> board();
    PageResult<AdminOrderRespVO> adminPage(OrderPageReqVO page);
    AdminOrderRespVO adminDetail(Long id);
    Map<String,Long> statistics(OrderPageReqVO page);
}
