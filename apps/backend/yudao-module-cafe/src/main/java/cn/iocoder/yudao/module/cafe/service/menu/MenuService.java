package cn.iocoder.yudao.module.cafe.service.menu;
import cn.iocoder.yudao.module.cafe.controller.app.menu.vo.MenuRespVO;
import cn.iocoder.yudao.module.cafe.controller.admin.menu.vo.*;
import java.util.List;
public interface MenuService {
    MenuRespVO getMenu(boolean includeDisabled);
    List<MenuRespVO.Group> getGroups();
    Long saveCategory(CategorySaveReqVO request);
    void deleteCategory(Long id);
    Long saveItem(MenuItemSaveReqVO request);
    void deleteItem(Long id);
    Long saveGroup(OptionGroupSaveReqVO request);
    void deleteGroup(Long id);
}
