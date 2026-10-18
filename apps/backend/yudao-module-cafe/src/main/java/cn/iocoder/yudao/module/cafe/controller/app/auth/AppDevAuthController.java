package cn.iocoder.yudao.module.cafe.controller.app.auth;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.module.cafe.controller.app.auth.vo.*;
import cn.iocoder.yudao.module.cafe.framework.CafeProperties;
import cn.iocoder.yudao.module.cafe.service.auth.StudentAuthService;
import jakarta.annotation.Resource;
import jakarta.annotation.security.PermitAll;
import jakarta.validation.Valid;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.DEV_LOGIN_UNAUTHORIZED;
@RestController @RequestMapping("/cafe/auth") @ConditionalOnProperty(name="cafe.auth.dev-login-enabled",havingValue="true")
public class AppDevAuthController {
    @Resource private StudentAuthService service;
    @Resource private CafeProperties properties;
    @PostMapping("/dev-login") @PermitAll
    public CommonResult<AuthLoginRespVO> login(
            @RequestHeader(value="X-Cafe-Dev-Secret", required=false) String suppliedSecret,
            @RequestBody @Valid DevLoginReqVO request) {
        String expectedSecret=properties.getAuth().getDevLoginSecret();
        if(expectedSecret==null||expectedSecret.length()<32||suppliedSecret==null
                ||!MessageDigest.isEqual(suppliedSecret.getBytes(StandardCharsets.UTF_8),
                expectedSecret.getBytes(StandardCharsets.UTF_8))){
            throw exception(DEV_LOGIN_UNAUTHORIZED);
        }
        return success(service.devLogin(request.getStudentNo(),request.getName()));
    }
}
