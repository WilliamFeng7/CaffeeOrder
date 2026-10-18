package cn.iocoder.yudao.module.cafe.controller.app.auth;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.module.cafe.controller.app.auth.vo.*;
import cn.iocoder.yudao.module.cafe.framework.CafeProperties;
import cn.iocoder.yudao.module.cafe.service.auth.StudentAuthService;
import jakarta.annotation.Resource;
import jakarta.annotation.security.PermitAll;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
@RestController @RequestMapping("/cafe/auth") public class AppAuthController {
    @Resource private CafeProperties properties;
    @Resource private StudentAuthService service;
    @GetMapping("/dingtalk-config") @PermitAll public CommonResult<Map<String,Object>> config(){return success(Map.of(
            "corpId",properties.getDingtalk().getCorpId(),
            "passwordLoginEnabled",properties.getAuth().isPasswordLoginEnabled()));}
    @PostMapping("/dingtalk-login") @PermitAll public CommonResult<AuthLoginRespVO> login(@RequestBody @Valid DingTalkLoginReqVO request){return success(service.dingTalkLogin(request.getAuthCode()));}
}
