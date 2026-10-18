package cn.iocoder.yudao.module.system.service.auth;
import cn.iocoder.yudao.module.system.controller.admin.auth.vo.*;
import cn.iocoder.yudao.module.system.dal.dataobject.user.AdminUserDO;
public interface AdminAuthService {
    AdminUserDO authenticate(String username, String password);
    AuthLoginRespVO login(AuthLoginReqVO reqVO);
    void logout(String token, Integer logType);
    AuthLoginRespVO refreshToken(String refreshToken);
}
