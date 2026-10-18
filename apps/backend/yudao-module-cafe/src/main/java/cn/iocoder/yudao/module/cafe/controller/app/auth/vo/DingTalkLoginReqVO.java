package cn.iocoder.yudao.module.cafe.controller.app.auth.vo;
import lombok.Data;
import jakarta.validation.constraints.*;
@Data public class DingTalkLoginReqVO { @NotBlank @Size(max=2048) private String authCode; }
