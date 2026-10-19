package cn.iocoder.yudao.module.system.service.auth;

import cn.iocoder.yudao.framework.common.exception.ServiceException;
import cn.iocoder.yudao.module.system.dal.dataobject.user.AdminUserDO;
import cn.iocoder.yudao.module.system.service.logger.LoginLogService;
import cn.iocoder.yudao.module.system.service.oauth2.OAuth2TokenService;
import cn.iocoder.yudao.module.system.service.user.AdminUserService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AdminAuthServiceImplSecurityTest {
    @Mock AdminUserService users;
    @Mock OAuth2TokenService tokens;
    @Mock LoginLogService logs;
    @Mock LoginRateLimiter limiter;
    @InjectMocks AdminAuthServiceImpl service;

    @Test void simpleLetterAndDigitPasswordCanAuthenticate() {
        var admin = new AdminUserDO().setId(1L).setUsername("admin").setPassword("hash").setStatus(0);
        when(users.getUserByUsername("admin")).thenReturn(admin);
        when(users.isPasswordMatch("admin123", "hash")).thenReturn(true);

        assertSame(admin, service.authenticate("admin", "admin123"));
        verify(limiter).reset("admin");
    }

    @Test void wrongPasswordIsStillRejected() {
        var admin = new AdminUserDO().setId(1L).setUsername("admin").setPassword("hash").setStatus(0);
        when(users.getUserByUsername("admin")).thenReturn(admin);
        when(users.isPasswordMatch("wrong123", "hash")).thenReturn(false);

        assertThrows(ServiceException.class, () -> service.authenticate("admin", "wrong123"));
        verify(limiter, never()).reset(anyString());
    }
}
