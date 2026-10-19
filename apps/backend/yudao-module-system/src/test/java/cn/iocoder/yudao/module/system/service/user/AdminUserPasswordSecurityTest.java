package cn.iocoder.yudao.module.system.service.user;

import cn.iocoder.yudao.framework.common.enums.UserTypeEnum;
import cn.iocoder.yudao.module.system.controller.admin.user.vo.profile.UserProfileUpdatePasswordReqVO;
import cn.iocoder.yudao.module.system.dal.dataobject.user.AdminUserDO;
import cn.iocoder.yudao.module.system.dal.mysql.user.AdminUserMapper;
import cn.iocoder.yudao.module.system.service.oauth2.OAuth2TokenService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.ArgumentCaptor;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AdminUserPasswordSecurityTest {

    @Mock AdminUserMapper userMapper;
    @Mock PasswordEncoder passwordEncoder;
    @Mock OAuth2TokenService oauth2TokenService;
    @InjectMocks AdminUserServiceImpl service;

    @BeforeEach
    void userExists() {
        when(userMapper.selectById(1L)).thenReturn(new AdminUserDO().setId(1L).setPassword("old-hash"));
        when(passwordEncoder.encode(anyString())).thenReturn("new-hash");
    }

    @Test
    void resetPasswordRevokesExistingSessions() {
        service.updateUserPassword(1L, "new-pass1");

        ArgumentCaptor<AdminUserDO> update = ArgumentCaptor.forClass(AdminUserDO.class);
        verify(userMapper).updateById(update.capture());
        assertEquals(1L, update.getValue().getId());
        assertEquals("new-hash", update.getValue().getPassword());
        verify(oauth2TokenService).removeAccessToken(1L, UserTypeEnum.ADMIN.getValue());
    }

    @Test
    void profilePasswordChangeRevokesExistingSessions() {
        when(passwordEncoder.matches("old-password", "old-hash")).thenReturn(true);
        UserProfileUpdatePasswordReqVO request = new UserProfileUpdatePasswordReqVO();
        request.setOldPassword("old-password");
        request.setNewPassword("new-pass1");

        service.updateUserPassword(1L, request);

        ArgumentCaptor<AdminUserDO> update = ArgumentCaptor.forClass(AdminUserDO.class);
        verify(userMapper).updateById(update.capture());
        assertEquals(1L, update.getValue().getId());
        assertEquals("new-hash", update.getValue().getPassword());
        verify(oauth2TokenService).removeAccessToken(1L, UserTypeEnum.ADMIN.getValue());
    }
}
