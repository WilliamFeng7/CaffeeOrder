package cn.iocoder.yudao.module.system.service.auth;

import cn.iocoder.yudao.module.system.dal.dataobject.user.AdminUserDO;
import cn.iocoder.yudao.module.system.service.user.AdminUserService;
import org.junit.jupiter.api.Test;
import org.springframework.boot.DefaultApplicationArguments;
import org.springframework.core.env.Environment;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.*;

class AdminBootstrapInitializerSecurityTest {

    @Test void firstStartFailsClosedWithoutExplicitPassword() {
        AdminUserService users = mock(AdminUserService.class);
        Environment environment = mock(Environment.class);
        when(users.getUser(1L)).thenReturn(new AdminUserDO().setId(1L).setPassword(""));

        assertThrows(IllegalStateException.class,
                () -> new AdminBootstrapInitializer(users, environment).run(new DefaultApplicationArguments()));
        verify(users, never()).updateUserPassword(anyLong(), anyString());
    }

    @Test void explicitOperatorPasswordRotatesBlankBootstrapAccount() {
        AdminUserService users = mock(AdminUserService.class);
        Environment environment = mock(Environment.class);
        when(environment.getProperty("OTIA_ADMIN_INITIAL_PASSWORD")).thenReturn("DemoPass123456");
        when(users.getUser(1L)).thenReturn(new AdminUserDO().setId(1L).setPassword(""));

        new AdminBootstrapInitializer(users, environment).run(new DefaultApplicationArguments());

        verify(users).updateUserPassword(1L, "DemoPass123456");
    }

    @Test void customizedPasswordIsNeverOverwritten() {
        AdminUserService users = mock(AdminUserService.class);
        Environment environment = mock(Environment.class);
        when(users.getUser(1L)).thenReturn(new AdminUserDO().setId(1L).setPassword("custom-hash"));

        new AdminBootstrapInitializer(users, environment).run(new DefaultApplicationArguments());

        verify(users, never()).updateUserPassword(anyLong(), anyString());
    }
}
