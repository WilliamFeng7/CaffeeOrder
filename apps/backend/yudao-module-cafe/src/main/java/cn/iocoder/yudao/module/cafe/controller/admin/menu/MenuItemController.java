package cn.iocoder.yudao.module.cafe.controller.admin.menu;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.module.cafe.controller.admin.menu.vo.*;
import cn.iocoder.yudao.module.cafe.controller.app.menu.vo.MenuRespVO;
import cn.iocoder.yudao.module.cafe.service.menu.MenuService;
import jakarta.annotation.Resource;
import jakarta.validation.Valid;
import org.springframework.validation.annotation.Validated;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
@RestController @Validated @RequestMapping("/cafe/menu-item") public class MenuItemController {
    @Resource private MenuService service;
    @GetMapping("/list") @PreAuthorize("@ss.hasPermission('cafe:menu:query')") public CommonResult<List<MenuRespVO.Item>> list(){return success(service.getMenu(true).getItems());}
    @PostMapping("/create") @PreAuthorize("@ss.hasPermission('cafe:menu:update')") public CommonResult<Long> create(@RequestBody @Valid MenuItemSaveReqVO request){request.setId(null);return success(service.saveItem(request));}
    @PutMapping("/update") @PreAuthorize("@ss.hasPermission('cafe:menu:update')") public CommonResult<Boolean> update(@RequestBody @Valid MenuItemSaveReqVO request){
        if(request.getId()==null)throw new IllegalArgumentException("编号不能为空");service.saveItem(request);return success(true);
    }
    @DeleteMapping("/delete") @PreAuthorize("@ss.hasPermission('cafe:menu:update')") public CommonResult<Boolean> delete(@RequestParam("id") Long id){service.deleteItem(id);return success(true);}
}
