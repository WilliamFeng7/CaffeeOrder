package cn.iocoder.yudao.module.cafe.dal.dataobject;
import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.*;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.*;
import java.time.*;
import java.util.*;
@Data @EqualsAndHashCode(callSuper=true) @TableName(value="cafe_option",autoResultMap=true)
public class OptionDO extends BaseDO {
    @TableId(type=IdType.AUTO) private Long id;
    private Long groupId;
    private String name;
    private String nameEn;
    private Integer priceDelta;
    private Boolean isDefault;
    private Integer sort;

}
