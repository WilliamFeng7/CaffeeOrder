package cn.iocoder.yudao.module.cafe.dal.dataobject;
import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.*;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.*;
import java.time.*;
import java.util.*;
@Data @EqualsAndHashCode(callSuper=true) @TableName(value="cafe_student",autoResultMap=true)
public class StudentDO extends BaseDO {
    @TableId(type=IdType.AUTO) private Long id;
    private String studentNo;
    private String name;
    private String dingtalkUserId;
    private String passwordHash;
    private LocalDateTime firstLoginTime;
    private LocalDateTime lastLoginTime;

}
