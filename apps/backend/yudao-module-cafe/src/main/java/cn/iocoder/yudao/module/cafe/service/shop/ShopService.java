package cn.iocoder.yudao.module.cafe.service.shop;
import cn.iocoder.yudao.module.cafe.dal.dataobject.ShopDO;
import cn.iocoder.yudao.module.cafe.controller.admin.menu.vo.ShopSaveReqVO;
public interface ShopService {
    ShopDO getShop();
    boolean canOrder();
    void update(ShopSaveReqVO request);
}
