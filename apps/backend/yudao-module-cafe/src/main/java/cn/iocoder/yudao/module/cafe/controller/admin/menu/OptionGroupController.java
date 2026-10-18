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
@RestController @Validated @RequestMapping("/cafe/option-group") public class OptionGroupController {
    @Resource private MenuService service;
    @GetMapping("/list") @PreAuthorize("@ss.hasPermission('cafe:menu:query')") public CommonResult<List<MenuRespVO.Group>> list(){return success(service.getGroups());}
    @PostMapping("/create") @PreAuthorize("@ss.hasPermission('cafe:menu:update')") public CommonResult<Long> create(@RequestBody @Valid OptionGroupSaveReqVO request){request.setId(null);return success(service.saveGroup(request));}
    @PutMapping("/update") @PreAuthorize("@ss.hasPermission('cafe:menu:update')") public CommonResult<Boolean> update(@RequestBody @Valid OptionGroupSaveReqVO request){
        if(request.getId()==null)throw new IllegalArgumentException("编号不能为空");service.saveGroup(request);return success(true);
    }
    @DeleteMapping("/delete") @PreAuthorize("@ss.hasPermission('cafe:menu:update')") public CommonResult<Boolean> delete(@RequestParam("id") Long id){service.deleteGroup(id);return success(true);}
}
