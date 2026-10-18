package cn.iocoder.yudao.module.system.controller.admin.auth.vo;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class RefreshTokenReqVO {

    @NotBlank
    @Size(max = 64)
    private String refreshToken;
}
