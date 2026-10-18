package cn.iocoder.yudao.module.cafe.controller.admin.barista.vo;
import jakarta.validation.constraints.*;
import lombok.Data;
@Data public class OrderEnterReqVO { @NotNull @Positive private Long id; @NotBlank(message="收银单号不能为空") @Size(max=80) private String posOrderNo; }
