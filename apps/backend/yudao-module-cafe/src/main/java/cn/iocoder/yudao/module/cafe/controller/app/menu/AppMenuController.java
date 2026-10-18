package cn.iocoder.yudao.module.cafe.controller.app.menu;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.module.cafe.controller.app.menu.vo.MenuRespVO;
import cn.iocoder.yudao.module.cafe.service.menu.MenuService;
import cn.iocoder.yudao.module.cafe.service.shop.ShopService;
import jakarta.annotation.Resource;
import jakarta.annotation.security.PermitAll;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
@RestController @RequestMapping("/cafe") public class AppMenuController {
    @Resource private MenuService menus;
    @Resource private ShopService shop;
    @GetMapping("/menu") @PermitAll public CommonResult<MenuRespVO> menu(){return success(menus.getMenu(false));}
    @GetMapping("/shop/status") @PermitAll public CommonResult<Map<String,Object>> status(){
        var settings=shop.getShop();return success(Map.of("open",shop.canOrder(),"banner",settings.getBanner(),"businessHours",settings.getBusinessHours()));
    }
}
