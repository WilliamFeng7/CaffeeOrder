package cn.iocoder.yudao.module.cafe.controller.app.auth.vo;
import lombok.Data;
import java.time.LocalDateTime;
@Data public class AuthLoginRespVO {private String accessToken;private LocalDateTime expiresTime;private String studentNo;private String name;}
