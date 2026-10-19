package cn.iocoder.yudao.module.system.service.user;

import cn.iocoder.yudao.framework.common.enums.CommonStatusEnum;
import cn.iocoder.yudao.module.infra.api.config.ConfigApi;
import cn.iocoder.yudao.module.system.controller.admin.user.vo.user.UserImportExcelVO;
import cn.iocoder.yudao.module.system.dal.dataobject.user.AdminUserDO;
import cn.iocoder.yudao.module.system.dal.mysql.user.AdminUserMapper;
import cn.iocoder.yudao.module.system.dal.mysql.dept.UserPostMapper;
import cn.iocoder.yudao.module.system.service.dept.DeptService;
import cn.iocoder.yudao.module.system.service.dept.PostService;
import cn.iocoder.yudao.module.system.service.oauth2.OAuth2TokenService;
import cn.iocoder.yudao.module.system.service.permission.PermissionService;
import cn.iocoder.yudao.module.system.service.permission.RoleService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Collections;
import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AdminUserImportSecurityTest {
    @Mock AdminUserMapper userMapper;
    @Mock DeptService deptService;
    @Mock PostService postService;
    @Mock PermissionService permissionService;
    @Mock RoleService roleService;
    @Mock PasswordEncoder passwordEncoder;
    @Mock OAuth2TokenService oauth2TokenService;
    @Mock UserPostMapper userPostMapper;
    @Mock ConfigApi configApi;
    @InjectMocks AdminUserServiceImpl service;

    @Test void disablingExistingUserThroughImportRevokesAllAdminTokens() {
        var existing = new AdminUserDO().setId(7L).setUsername("barista1").setStatus(CommonStatusEnum.ENABLE.getStatus());
        var imported = new UserImportExcelVO().setUsername("barista1").setNickname("Barista")
                .setDeptId(1L).setStatus(CommonStatusEnum.DISABLE.getStatus());
        when(configApi.getConfigValueByKey(AdminUserServiceImpl.USER_INIT_PASSWORD_KEY)).thenReturn("safe-Initial1");
        when(userMapper.selectByUsername("barista1")).thenReturn(existing);
        when(permissionService.getUserRoleIdListByUserId(7L)).thenReturn(Collections.emptySet());

        service.importUserList(List.of(imported), true);

        verify(userMapper).updateById(argThat((AdminUserDO update) -> update.getId().equals(7L)
                && CommonStatusEnum.DISABLE.getStatus().equals(update.getStatus())));
        verify(oauth2TokenService).removeAccessToken(7L, cn.iocoder.yudao.framework.common.enums.UserTypeEnum.ADMIN.getValue());
    }

    @Test void importPasswordMustContainLettersAndDigits() {
        when(configApi.getConfigValueByKey(AdminUserServiceImpl.USER_INIT_PASSWORD_KEY)).thenReturn("12345678");

        org.junit.jupiter.api.Assertions.assertThrows(cn.iocoder.yudao.framework.common.exception.ServiceException.class,
                () -> service.importUserList(List.of(new UserImportExcelVO()), false));

        verifyNoInteractions(userMapper, oauth2TokenService);
    }
}
