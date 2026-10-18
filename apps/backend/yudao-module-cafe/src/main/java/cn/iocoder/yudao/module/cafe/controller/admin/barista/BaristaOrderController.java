package cn.iocoder.yudao.module.cafe.controller.admin.barista;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.module.cafe.controller.admin.barista.vo.*;
import cn.iocoder.yudao.module.cafe.service.order.*;
import jakarta.annotation.Resource;
import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
@RestController @RequestMapping("/cafe/barista/order") public class BaristaOrderController {
    @Resource private OrderService service;
    @Resource private OrderQueryService query;
    @GetMapping("/board") @PreAuthorize("@ss.hasPermission('cafe:barista:query')") public CommonResult<Map<String,List<BaristaOrderRespVO>>> board(){return success(query.board());}
    @PutMapping("/enter") @PreAuthorize("@ss.hasPermission('cafe:barista:update')") public CommonResult<Boolean> enter(@RequestBody @Valid OrderEnterReqVO request){service.enter(request.getId(),request.getPosOrderNo());return success(true);}
    @PutMapping("/done") @PreAuthorize("@ss.hasPermission('cafe:barista:update')") public CommonResult<Boolean> done(@RequestBody @Valid OrderIdReqVO request){service.done(request.getId());return success(true);}
    @PutMapping("/undo-done") @PreAuthorize("@ss.hasPermission('cafe:barista:update')") public CommonResult<Boolean> undo(@RequestBody @Valid OrderIdReqVO request){service.undoDone(request.getId());return success(true);}
}
