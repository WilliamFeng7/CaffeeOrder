package cn.iocoder.yudao.module.cafe.framework;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import lombok.Data;
import lombok.ToString;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;
@Data @Validated @ConfigurationProperties("cafe")
public class CafeProperties {
    @Valid private Auth auth = new Auth();
    @Valid private Card card = new Card();
    @Valid private Order order = new Order();
    @Valid private DingTalk dingtalk = new DingTalk();
    @Data public static class Auth {
        private boolean devLoginEnabled = false;
        @ToString.Exclude private String devLoginSecret = "";
        private boolean passwordLoginEnabled = false;
        private String bootstrapStudentNo = "";
        private String bootstrapStudentName = "测试学生";
        @ToString.Exclude private String bootstrapStudentPassword = "";
    }
    @Data public static class Card { private boolean mockEnabled = false; @Min(0) private int defaultBalance = 50000; }
    @Data public static class Order {
        @Min(1) @Max(100) private int maxCups = 10;
        @Min(60) private int paymentTimeoutSeconds = 180;
    }
    @Data public static class DingTalk {
        private String corpId = "";
        private String appKey = "";
        private String appSecret = "";
        @NotBlank private String studentNoField = "job_number";
    }
}
