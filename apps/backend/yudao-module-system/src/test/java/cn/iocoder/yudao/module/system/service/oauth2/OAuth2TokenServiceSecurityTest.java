package cn.iocoder.yudao.module.system.service.oauth2;

import cn.iocoder.yudao.framework.common.enums.UserTypeEnum;
import cn.iocoder.yudao.module.system.dal.dataobject.oauth2.OAuth2AccessTokenDO;
import cn.iocoder.yudao.module.system.dal.dataobject.oauth2.OAuth2RefreshTokenDO;
import cn.iocoder.yudao.module.system.dal.dataobject.user.AdminUserDO;
import cn.iocoder.yudao.module.system.dal.mysql.oauth2.OAuth2AccessTokenMapper;
import cn.iocoder.yudao.module.system.dal.mysql.oauth2.OAuth2RefreshTokenMapper;
import cn.iocoder.yudao.module.system.dal.redis.oauth2.OAuth2AccessTokenRedisDAO;
import cn.iocoder.yudao.module.system.service.oauth2.OAuth2ClientService;
import cn.iocoder.yudao.module.system.service.user.AdminUserService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.ArgumentCaptor;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class OAuth2TokenServiceSecurityTest {
    @Mock OAuth2AccessTokenMapper accessTokens;
    @Mock OAuth2RefreshTokenMapper refreshTokens;
    @Mock OAuth2AccessTokenRedisDAO redis;
    @Mock OAuth2ClientService clients;
    @Mock AdminUserService users;
    @InjectMocks OAuth2TokenServiceImpl service;

    @Test void disabledAdminAccessTokenIsRejectedEvenWhenCached() {
        when(redis.get("access")).thenReturn(new OAuth2AccessTokenDO().setAccessToken("access")
                .setUserId(7L).setUserType(UserTypeEnum.ADMIN.getValue()).setExpiresTime(LocalDateTime.now().plusMinutes(5)));
        doThrow(new IllegalStateException("disabled")).when(users).validateUser(7L);

        assertThrows(IllegalStateException.class, () -> service.checkAccessToken("access"));
    }

    @Test void disabledAdminCannotRefresh() {
        when(refreshTokens.selectByRefreshToken("refresh")).thenReturn(new OAuth2RefreshTokenDO()
                .setRefreshToken("refresh").setUserId(7L).setUserType(UserTypeEnum.ADMIN.getValue())
                .setClientId("default").setExpiresTime(LocalDateTime.now().plusDays(1)));
        when(clients.validOAuthClientFromCache("default")).thenReturn(new cn.iocoder.yudao.module.system.dal.dataobject.oauth2.OAuth2ClientDO().setClientId("default"));
        doThrow(new IllegalStateException("disabled")).when(users).validateUserForUpdate(7L);

        assertThrows(IllegalStateException.class, () -> service.refreshAccessToken("refresh", "default"));
        verify(accessTokens, never()).selectListByRefreshToken(anyString());
    }

    @Test void memberAccessTokenDoesNotUseAdminStatusLookup() {
        when(redis.get("member-access")).thenReturn(new OAuth2AccessTokenDO().setAccessToken("member-access")
                .setUserId(9L).setUserType(UserTypeEnum.MEMBER.getValue()).setExpiresTime(LocalDateTime.now().plusMinutes(5)));

        assertNotNull(service.checkAccessToken("member-access"));
        verifyNoInteractions(users);
    }

    @Test void sessionRevocationDeletesRefreshTokensWithoutAccessTokenRows() {
        when(accessTokens.selectListByUserIdAndUserType(7L, UserTypeEnum.ADMIN.getValue()))
                .thenReturn(List.of());

        service.removeAccessToken(7L, UserTypeEnum.ADMIN.getValue());

        verify(refreshTokens).deleteByUserIdAndUserType(7L, UserTypeEnum.ADMIN.getValue());
    }

    @Test void refreshTokenCannotBeUsedAsBearerAccessToken() {
        when(redis.get("refresh")).thenReturn(null);
        when(accessTokens.selectByAccessToken("refresh")).thenReturn(null);

        assertNull(service.getAccessToken("refresh"));
        verify(refreshTokens, never()).selectByRefreshToken(anyString());
    }

    @Test void refreshConsumesAndRotatesRefreshToken() {
        OAuth2RefreshTokenDO oldRefresh = new OAuth2RefreshTokenDO()
                .setId(10L).setRefreshToken("old-refresh").setUserId(9L)
                .setUserType(UserTypeEnum.MEMBER.getValue()).setClientId("default")
                .setScopes(List.of()).setExpiresTime(LocalDateTime.now().plusDays(1));
        when(refreshTokens.selectByRefreshToken("old-refresh")).thenReturn(oldRefresh);
        when(clients.validOAuthClientFromCache("default")).thenReturn(
                new cn.iocoder.yudao.module.system.dal.dataobject.oauth2.OAuth2ClientDO()
                        .setClientId("default").setAccessTokenValiditySeconds(1800)
                        .setRefreshTokenValiditySeconds(86400));
        when(refreshTokens.deleteById(10L)).thenReturn(1);
        when(accessTokens.selectListByRefreshToken("old-refresh")).thenReturn(List.of());

        OAuth2AccessTokenDO created = service.refreshAccessToken("old-refresh", "default");

        verify(refreshTokens).deleteById(10L);
        ArgumentCaptor<OAuth2RefreshTokenDO> rotated = ArgumentCaptor.forClass(OAuth2RefreshTokenDO.class);
        verify(refreshTokens).insert(rotated.capture());
        assertNotEquals("old-refresh", rotated.getValue().getRefreshToken());
        assertEquals(rotated.getValue().getRefreshToken(), created.getRefreshToken());
    }

    @Test void losingConcurrentRefreshCannotMintAnotherTokenPair() {
        OAuth2RefreshTokenDO oldRefresh = new OAuth2RefreshTokenDO()
                .setId(10L).setRefreshToken("old-refresh").setUserId(9L)
                .setUserType(UserTypeEnum.MEMBER.getValue()).setClientId("default")
                .setScopes(List.of()).setExpiresTime(LocalDateTime.now().plusDays(1));
        when(refreshTokens.selectByRefreshToken("old-refresh")).thenReturn(oldRefresh);
        when(clients.validOAuthClientFromCache("default")).thenReturn(
                new cn.iocoder.yudao.module.system.dal.dataobject.oauth2.OAuth2ClientDO()
                        .setClientId("default").setAccessTokenValiditySeconds(1800)
                        .setRefreshTokenValiditySeconds(86400));
        when(refreshTokens.deleteById(10L)).thenReturn(0);

        assertThrows(Exception.class, () -> service.refreshAccessToken("old-refresh", "default"));

        verify(refreshTokens, never()).insert(any(OAuth2RefreshTokenDO.class));
        verify(accessTokens, never()).insert(any(OAuth2AccessTokenDO.class));
    }
}
