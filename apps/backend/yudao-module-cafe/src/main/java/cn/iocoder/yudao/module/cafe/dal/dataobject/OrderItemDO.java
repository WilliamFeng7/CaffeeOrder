package cn.iocoder.yudao.module.cafe.dal.dataobject;
import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.*;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.*;
import java.time.*;
import java.util.*;
@Data @EqualsAndHashCode(callSuper=true) @TableName(value="cafe_order_item",autoResultMap=true)
public class OrderItemDO extends BaseDO {
    @TableId(type=IdType.AUTO) private Long id;
    private Long orderId;
    private Long itemId;
    private String name;
    private String nameEn;
    private String imageUrl;
    private Integer unitPrice;
    private Integer quantity;
    private String optionsText;
    @TableField(typeHandler=JacksonTypeHandler.class) private List<OptionSnapshot> options;
    @Data @NoArgsConstructor @AllArgsConstructor public static class OptionSnapshot {
        private String groupName;
        private String groupNameEn;
        private String name;
        private String nameEn;
    }
}
