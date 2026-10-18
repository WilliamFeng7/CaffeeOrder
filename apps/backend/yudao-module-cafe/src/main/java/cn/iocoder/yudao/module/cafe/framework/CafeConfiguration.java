package cn.iocoder.yudao.module.cafe.framework;
import cn.iocoder.yudao.module.cafe.service.card.*;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.autoconfigure.condition.*;
import org.springframework.context.annotation.*;
import org.springframework.core.env.Environment;
import org.springframework.scheduling.annotation.EnableScheduling;
import java.time.*;
import java.util.Arrays;
import java.util.Set;
@Configuration @EnableScheduling @EnableConfigurationProperties(CafeProperties.class)
public class CafeConfiguration {
    public static final ZoneId ZONE = ZoneId.of("Asia/Shanghai");
    @Bean public Clock cafeClock() { return Clock.system(ZONE); }
    @Bean @ConditionalOnProperty(name="cafe.card.mock-enabled", havingValue="true")
    public StudentCardClient mockStudentCardClient(CafeProperties properties) {
        return new MockStudentCardClient(properties.getCard().getDefaultBalance());
    }
    @Bean public Object cafeSafetyCheck(CafeProperties properties, Environment environment,
                                        org.springframework.beans.factory.ObjectProvider<StudentCardClient> clients) {
        // 允许名单而不是拒绝名单：只拦 prod/production 会被换个名字绕过（staging、prod-cn 等），
        // 学号直登和 mock 学生卡只允许恰好激活 dev 一种配置的环境。
        if (properties.getAuth().isDevLoginEnabled() || properties.getCard().isMockEnabled()) {
            if (!Set.of("dev").equals(Set.of(environment.getActiveProfiles()))) {
                throw new IllegalStateException("学号直登和 mock 学生卡只允许 dev 配置，当前激活: "
                        + Arrays.toString(environment.getActiveProfiles()));
            }
        }
        if (clients.getIfAvailable() == null) {
            throw new IllegalStateException("未配置真实 StudentCardClient；仅本地开发可打开 cafe.card.mock-enabled");
        }
        return new Object();
    }
}
