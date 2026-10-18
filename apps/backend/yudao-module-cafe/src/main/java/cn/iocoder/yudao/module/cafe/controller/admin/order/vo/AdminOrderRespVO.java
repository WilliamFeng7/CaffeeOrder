package cn.iocoder.yudao.module.cafe.controller.admin.order.vo;
import cn.iocoder.yudao.module.cafe.controller.app.order.vo.OrderRespVO;
import lombok.*;
@Data @EqualsAndHashCode(callSuper=true) public class AdminOrderRespVO extends OrderRespVO {
    private String studentNo; private String studentName; private Integer cupCount; private String failureReason;
}
