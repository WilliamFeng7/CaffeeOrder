package cn.iocoder.yudao.module.cafe.controller.app.order.vo;
import lombok.Data;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.List;
@Data public class OrderCreateReqVO {
    @Valid @NotEmpty @Size(max=100) private List<Item> items;
    @Data public static class Item {
        @NotNull @Positive private Long itemId;
        @NotNull @Min(1) @Max(100) private Integer quantity;
        @NotNull @Size(max=10) private List<@NotNull @Positive Long> optionIds;
    }
}
