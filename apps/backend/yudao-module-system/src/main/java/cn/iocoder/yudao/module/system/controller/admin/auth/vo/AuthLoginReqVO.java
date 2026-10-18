package cn.iocoder.yudao.module.system.controller.admin.auth.vo;
import jakarta.validation.constraints.*;
import lombok.Data;
@Data
public class AuthLoginReqVO {
    @NotBlank(message = "登录账号不能为空") @Size(min = 4, max = 30) private String username;
    @NotBlank(message = "密码不能为空") @Size(min = 4, max = 64) private String password;
}
