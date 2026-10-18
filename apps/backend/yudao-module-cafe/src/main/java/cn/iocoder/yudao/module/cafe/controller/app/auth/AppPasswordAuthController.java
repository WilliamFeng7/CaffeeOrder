package cn.iocoder.yudao.module.cafe.controller.app.auth;

import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.module.cafe.controller.app.auth.vo.AuthLoginRespVO;
import cn.iocoder.yudao.module.cafe.controller.app.auth.vo.PasswordLoginReqVO;
import cn.iocoder.yudao.module.cafe.service.auth.StudentAuthService;
import jakarta.annotation.Resource;
import jakarta.annotation.security.PermitAll;
import jakarta.validation.Valid;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;

@RestController
@RequestMapping("/cafe/auth")
@ConditionalOnProperty(name = "cafe.auth.password-login-enabled", havingValue = "true")
public class AppPasswordAuthController {

    @Resource
    private StudentAuthService service;

    @PostMapping("/password-login")
    @PermitAll
    public CommonResult<AuthLoginRespVO> login(@RequestBody @Valid PasswordLoginReqVO request) {
        return success(service.passwordLogin(request.getStudentNo(), request.getPassword()));
    }
}
