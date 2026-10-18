package cn.iocoder.yudao.module.cafe;
import cn.iocoder.yudao.module.cafe.framework.CafeConfiguration;
import cn.iocoder.yudao.module.cafe.service.card.StudentCardClient;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import static org.assertj.core.api.Assertions.assertThat;
class CafeSafetyTest {
    @Test void noCardImplementationFailsClosed(){new ApplicationContextRunner().withUserConfiguration(CafeConfiguration.class).run(context->assertThat(context).hasFailed());}
    // 守护是允许名单：只要不是恰好 dev 一种配置，学号直登和 mock 学生卡一律拒绝启动。
    @Test void nonDevProfilesCannotUseFakeCardOrDevLogin(){
        for (String[] profiles : new String[][]{{"prod"},{"production"},{"staging"},{"local"},{"prod-cn"},{"prod","dev"}}) {
            new ApplicationContextRunner().withUserConfiguration(CafeConfiguration.class)
                .withInitializer(context->context.getEnvironment().setActiveProfiles(profiles))
                .withPropertyValues("cafe.card.mock-enabled=true","cafe.auth.dev-login-enabled=true")
                .run(context->assertThat(context).hasFailed());
        }
    }
    @Test void devProfileAllowsExplicitMock(){new ApplicationContextRunner().withUserConfiguration(CafeConfiguration.class).withInitializer(context->context.getEnvironment().setActiveProfiles("dev")).withPropertyValues("cafe.card.mock-enabled=true").run(context->{assertThat(context).hasNotFailed();assertThat(context).hasSingleBean(StudentCardClient.class);});}
    @Test void mockWithoutDevProfileFails(){new ApplicationContextRunner().withUserConfiguration(CafeConfiguration.class).withPropertyValues("cafe.card.mock-enabled=true").run(context->assertThat(context).hasFailed());}
}
