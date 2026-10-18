package cn.iocoder.yudao.module.cafe.controller.app.auth.vo;
import lombok.Data;
import jakarta.validation.constraints.*;
@Data public class DevLoginReqVO {
    @NotBlank @Pattern(regexp="[A-Za-z0-9_-]{1,40}",message="学号格式不正确") private String studentNo;
    @NotBlank @Size(max=80) private String name;
}
