package cn.iocoder.yudao.module.cafe.controller.admin.menu;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.module.cafe.controller.admin.menu.vo.ShopSaveReqVO;
import cn.iocoder.yudao.module.cafe.dal.dataobject.ShopDO;
import cn.iocoder.yudao.module.cafe.service.shop.ShopService;
import jakarta.annotation.Resource;
import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
@RestController @RequestMapping("/cafe/shop") public class ShopController {
    @Resource private ShopService service;
    @GetMapping("/get") @PreAuthorize("@ss.hasPermission('cafe:shop:query')") public CommonResult<ShopDO> get(){return success(service.getShop());}
    @PutMapping("/update") @PreAuthorize("@ss.hasPermission('cafe:shop:update')") public CommonResult<Boolean> update(@RequestBody @Valid ShopSaveReqVO request){service.update(request);return success(true);}
}
