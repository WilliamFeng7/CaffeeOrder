package cn.iocoder.yudao.module.cafe.controller.app.order.vo;
import cn.iocoder.yudao.module.cafe.dal.dataobject.OrderItemDO.OptionSnapshot;
import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;
@Data public class OrderRespVO {
    private Long id; private String orderNo; private Integer status; private String posOrderNo;
    private Integer aheadCount; private Integer totalPrice;
    private LocalDateTime createTime; private LocalDateTime enteredTime; private LocalDateTime doneTime;
    private List<Item> items;
    @Data public static class Item {
        private Long itemId; private String name; private String nameEn; private String imageUrl;
        private Integer unitPrice; private Integer quantity; private String optionsText; private List<OptionSnapshot> options;
    }
}
