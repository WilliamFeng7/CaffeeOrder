package cn.iocoder.yudao.module.cafe.controller.admin.barista.vo;
import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;
@Data public class BaristaOrderRespVO {
    private Long id;private String orderNo;private Integer status;private String posOrderNo;private String studentName;
    private LocalDateTime createTime;private LocalDateTime enteredTime;private LocalDateTime doneTime;
    private Integer totalPrice;private Integer cupCount;private List<Item> items;
    @Data public static class Item {private String name;private Integer quantity;private String optionsText;}
}
