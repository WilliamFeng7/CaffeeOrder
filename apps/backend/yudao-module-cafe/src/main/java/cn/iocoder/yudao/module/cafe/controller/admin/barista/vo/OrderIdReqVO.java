package cn.iocoder.yudao.module.cafe.controller.admin.barista.vo;
import jakarta.validation.constraints.*;
import lombok.Data;
@Data public class OrderIdReqVO { @NotNull @Positive private Long id; }
