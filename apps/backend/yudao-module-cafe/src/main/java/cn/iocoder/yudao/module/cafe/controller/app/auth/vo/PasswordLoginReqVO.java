package cn.iocoder.yudao.module.cafe.controller.app.auth.vo;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class PasswordLoginReqVO {

    @NotBlank
    @Pattern(regexp = "[A-Za-z0-9_-]{1,40}", message = "学号格式不正确")
    private String studentNo;

    @NotBlank
    @Size(max = 72)
    private String password;
}
