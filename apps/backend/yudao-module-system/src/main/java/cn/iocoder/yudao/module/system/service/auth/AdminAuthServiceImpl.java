package cn.iocoder.yudao.module.system.service.auth;
import cn.iocoder.yudao.framework.common.enums.*;
import cn.iocoder.yudao.framework.common.util.object.BeanUtils;
import cn.iocoder.yudao.framework.common.util.servlet.ServletUtils;
import cn.iocoder.yudao.framework.datapermission.core.annotation.DataPermission;
import cn.iocoder.yudao.module.system.api.logger.dto.LoginLogCreateReqDTO;
import cn.iocoder.yudao.module.system.controller.admin.auth.vo.*;
import cn.iocoder.yudao.module.system.dal.dataobject.oauth2.OAuth2AccessTokenDO;
import cn.iocoder.yudao.module.system.dal.dataobject.user.AdminUserDO;
import cn.iocoder.yudao.module.system.enums.logger.*;
import cn.iocoder.yudao.module.system.enums.oauth2.OAuth2ClientConstants;
import cn.iocoder.yudao.module.system.service.logger.LoginLogService;
import cn.iocoder.yudao.module.system.service.oauth2.OAuth2TokenService;
import cn.iocoder.yudao.module.system.service.user.AdminUserService;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;
import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.system.enums.ErrorCodeConstants.*;
/** 保留芋道账号密码认证、OAuth2 令牌和登录日志，移除短信、注册和社交登录。 */
@Service public class AdminAuthServiceImpl implements AdminAuthService {
    @Resource private AdminUserService userService;
    @Resource private OAuth2TokenService tokens;
    @Resource private LoginLogService logs;
    @Resource private LoginRateLimiter rateLimiter;
    public AdminUserDO authenticate(String username,String password){
        rateLimiter.check(username);
        var user=userService.getUserByUsername(username);
        // Preserve the seeded local super-admin flow, but never accept the
        // published import credential for a staff account.
        if(user==null||LegacyPasswordPolicy.isLegacySharedImportPassword(password)
                ||!userService.isPasswordMatch(password,user.getPassword())){
            log(user==null?null:user.getId(),username,LoginLogTypeEnum.LOGIN_USERNAME.getType(),LoginResultEnum.BAD_CREDENTIALS);
            throw exception(AUTH_LOGIN_BAD_CREDENTIALS);
        }
        if(CommonStatusEnum.isDisable(user.getStatus())){
            log(user.getId(),username,LoginLogTypeEnum.LOGIN_USERNAME.getType(),LoginResultEnum.USER_DISABLED);
            throw exception(AUTH_LOGIN_USER_DISABLED);
        }
        rateLimiter.reset(username);
        return user;
    }
    @DataPermission(enable=false)
    public AuthLoginRespVO login(AuthLoginReqVO request){
        var user=authenticate(request.getUsername(),request.getPassword());
        log(user.getId(),user.getUsername(),LoginLogTypeEnum.LOGIN_USERNAME.getType(),LoginResultEnum.SUCCESS);
        userService.updateUserLogin(user.getId(),ServletUtils.getClientIP());
        return BeanUtils.toBean(tokens.createAccessToken(user.getId(),UserTypeEnum.ADMIN.getValue(),OAuth2ClientConstants.CLIENT_ID_DEFAULT,null),AuthLoginRespVO.class);
    }
    public AuthLoginRespVO refreshToken(String refreshToken){return BeanUtils.toBean(tokens.refreshAccessToken(refreshToken,OAuth2ClientConstants.CLIENT_ID_DEFAULT),AuthLoginRespVO.class);}
    public void logout(String token,Integer logType){
        OAuth2AccessTokenDO access=tokens.removeAccessToken(token);
        if(access==null)return;
        var user=userService.getUser(access.getUserId());
        log(access.getUserId(),user==null?null:user.getUsername(),logType,LoginResultEnum.SUCCESS);
    }
    private void log(Long userId,String username,Integer type,LoginResultEnum result){
        LoginLogCreateReqDTO dto=new LoginLogCreateReqDTO();dto.setUserId(userId);dto.setUsername(username);dto.setLogType(type);
        dto.setUserType(UserTypeEnum.ADMIN.getValue());dto.setUserIp(ServletUtils.getClientIP());dto.setUserAgent(ServletUtils.getUserAgent());dto.setResult(result.getResult());dto.setTraceId("");logs.createLoginLog(dto);
    }
}
