package cn.iocoder.yudao.module.cafe.dal.dataobject;
import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.*;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.*;
import java.time.*;
import java.util.*;
@Data @EqualsAndHashCode(callSuper=true) @TableName(value="cafe_menu_item",autoResultMap=true)
public class MenuItemDO extends BaseDO {
    @TableId(type=IdType.AUTO) private Long id;
    private String name;
    private String nameEn;
    private String description;
    private String descriptionEn;
    private Integer price;
    private String categoryCode;
    private String imageUrl;
    private Boolean recommended;
    private Boolean enabled;
    private Boolean soldOut;
    private Integer sort;

}
