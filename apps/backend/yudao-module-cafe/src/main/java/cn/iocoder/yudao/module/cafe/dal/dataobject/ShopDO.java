package cn.iocoder.yudao.module.cafe.dal.dataobject;
import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.*;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.*;
import java.time.*;
import java.util.*;
@Data @EqualsAndHashCode(callSuper=true) @TableName(value="cafe_shop",autoResultMap=true)
public class ShopDO extends BaseDO {
    @TableId(type=IdType.AUTO) private Long id;
    private Boolean open;
    private String banner;
    @TableField(typeHandler=JacksonTypeHandler.class) private List<BusinessHour> businessHours;
    @Data public static class BusinessHour {
        private String start; private String end;
        public BusinessHour() {}
        public BusinessHour(String start,String end){this.start=start;this.end=end;}
    }
}
