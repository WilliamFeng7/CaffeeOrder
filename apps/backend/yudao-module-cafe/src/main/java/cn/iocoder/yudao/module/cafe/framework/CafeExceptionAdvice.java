package cn.iocoder.yudao.module.cafe.framework;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import org.springframework.core.annotation.Order;
import org.springframework.core.Ordered;
import org.springframework.web.bind.annotation.*;
@RestControllerAdvice(basePackages="cn.iocoder.yudao.module.cafe") @Order(Ordered.HIGHEST_PRECEDENCE)
public class CafeExceptionAdvice {
    @ExceptionHandler(IllegalArgumentException.class)
    public CommonResult<?> invalid(IllegalArgumentException ex){return CommonResult.error(400,ex.getMessage());}
}
