package cn.iocoder.yudao.module.cafe.controller.admin.order.vo;
import cn.iocoder.yudao.framework.common.pojo.PageParam;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.springframework.format.annotation.DateTimeFormat;
import jakarta.validation.constraints.*;
import java.time.LocalDate;
@Data @EqualsAndHashCode(callSuper=true) public class OrderPageReqVO extends PageParam {
    @DateTimeFormat(iso=DateTimeFormat.ISO.DATE) private LocalDate startDate;
    @DateTimeFormat(iso=DateTimeFormat.ISO.DATE) private LocalDate endDate;
    private Integer status;
    @Size(max=80) private String student;
    @Size(max=20) private String posOrderNo;
    @AssertTrue(message="结束日期不能早于开始日期") public boolean isDateRangeValid(){return startDate==null||endDate==null||!endDate.isBefore(startDate);}
    @AssertTrue(message="订单状态不正确") public boolean isStatusValid(){return status==null||java.util.Set.of(0,1,2,10,20,30).contains(status);}
}
