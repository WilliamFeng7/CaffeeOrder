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

    @Test void publicImportPasswordIsRejectedForImportedStaff() {
        var imported = new AdminUserDO().setId(2L).setUsername("barista1").setPassword("hash").setStatus(0);
        when(users.getUserByUsername("barista1")).thenReturn(imported);
        assertThrows(ServiceException.class, () -> service.authenticate("barista1", "admin123"));

        verify(limiter).check("barista1");
        verify(users, never()).isPasswordMatch(anyString(), anyString());
        verify(logs).createLoginLog(any());
        verify(limiter, never()).reset(anyString());
    }

    @Test void legacySharedPasswordIsRejectedForEveryAccount() {
        var admin = new AdminUserDO().setId(1L).setUsername("admin").setPassword("hash").setStatus(0);
        when(users.getUserByUsername("admin")).thenReturn(admin);

        assertThrows(ServiceException.class, () -> service.authenticate("admin", "admin123"));
        verify(users, never()).isPasswordMatch(anyString(), anyString());
        verify(limiter, never()).reset(anyString());
    }
}
