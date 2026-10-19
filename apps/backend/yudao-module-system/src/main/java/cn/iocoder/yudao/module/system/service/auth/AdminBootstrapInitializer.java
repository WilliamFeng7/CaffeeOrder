package cn.iocoder.yudao.module.system.service.auth;

import cn.iocoder.yudao.framework.common.util.validation.PasswordPolicyUtils;
import cn.iocoder.yudao.module.system.service.user.AdminUserService;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

/** 真实学生卡启用时，绝不允许初始 super_admin 继续使用公开默认密码。 */
@Component
public class AdminBootstrapInitializer implements ApplicationRunner {
    private final AdminUserService users;
    private final Environment environment;

    public AdminBootstrapInitializer(AdminUserService users, Environment environment) {
        this.users = users;
        this.environment = environment;
    }

    @Override
    public void run(ApplicationArguments args) {
        String configured = environment.getProperty("OTIA_ADMIN_INITIAL_PASSWORD");
        var admin = users.getUser(1L);
        if (admin == null || (admin.getPassword() != null && !admin.getPassword().isBlank())) return;

        if (configured != null && !PasswordPolicyUtils.isValid(configured)) {
            throw new IllegalStateException("OTIA_ADMIN_INITIAL_PASSWORD 必须满足："
                    + PasswordPolicyUtils.MESSAGE);
        }
        if (configured == null || configured.isBlank()) {
            throw new IllegalStateException("首次启动前必须配置 OTIA_ADMIN_INITIAL_PASSWORD（至少 8 位，"
                    + "且同时包含字母和数字）");
        }
        users.updateUserPassword(admin.getId(), configured);
    }
}
