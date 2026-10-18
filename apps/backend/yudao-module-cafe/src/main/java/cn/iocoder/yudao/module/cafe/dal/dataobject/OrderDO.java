package cn.iocoder.yudao.module.cafe.dal.dataobject;
import cn.iocoder.yudao.framework.mybatis.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.*;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.*;
import java.time.*;
import java.util.*;
@Data @EqualsAndHashCode(callSuper=true) @TableName(value="cafe_order",autoResultMap=true)
public class OrderDO extends BaseDO {
    @TableId(type=IdType.AUTO) private Long id;
    private String orderNo;
    private Long studentId;
    private String studentNo;
    private String studentName;
    private Integer status;
    private LocalDate businessDate;
    private String posOrderNo;
    private Integer totalPrice;
    private Integer cupCount;
    private LocalDateTime enteredTime;
    private LocalDateTime doneTime;
    private String failureReason;
    private String requestKey;
    private String fingerprint;
    private Integer version;
    private LocalDateTime retryAfter;

}
