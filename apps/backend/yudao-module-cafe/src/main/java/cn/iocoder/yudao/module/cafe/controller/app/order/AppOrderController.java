package cn.iocoder.yudao.module.cafe.controller.app.order;
import cn.iocoder.yudao.framework.common.pojo.*;
import cn.iocoder.yudao.module.cafe.controller.app.order.vo.*;
import cn.iocoder.yudao.module.cafe.service.order.*;
import jakarta.annotation.Resource;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
import static cn.iocoder.yudao.framework.security.core.util.SecurityFrameworkUtils.getLoginUserId;
@RestController @RequestMapping("/cafe/order") public class AppOrderController {
    @Resource private OrderService service;
    @Resource private OrderQueryService query;
    @PostMapping("/create") public CommonResult<OrderRespVO> create(@RequestBody @Valid OrderCreateReqVO request,@RequestHeader(value="Idempotency-Key",required=false) String key){
        Long student=getLoginUserId();return success(query.getStudentOrder(student,service.create(student,request,key)));
    }
    @GetMapping("/page") public CommonResult<PageResult<OrderRespVO>> page(@Valid PageParam page){return success(query.studentPage(getLoginUserId(),page));}
    @GetMapping("/queue") public CommonResult<Map<String,Long>> queue(){return success(Map.of("waitingCount",query.waitingCount()));}
}
