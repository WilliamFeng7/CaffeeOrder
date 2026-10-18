package cn.iocoder.yudao.module.cafe.service.order;
import cn.iocoder.yudao.module.cafe.controller.app.order.vo.OrderCreateReqVO;
public interface OrderService {
    Long create(Long studentId,OrderCreateReqVO request,String idempotencyKey);
    void enter(Long id,String posOrderNo);
    void done(Long id);
    void undoDone(Long id);
    void recoverPayments();
}
