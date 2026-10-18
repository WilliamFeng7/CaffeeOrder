package cn.iocoder.yudao.module.cafe;
import cn.iocoder.yudao.module.cafe.controller.app.menu.vo.MenuRespVO;
import cn.iocoder.yudao.module.cafe.controller.app.order.vo.OrderCreateReqVO;
import java.util.*;
public final class CafeTestData {
    public static MenuRespVO menu(){
        MenuRespVO menu=new MenuRespVO();MenuRespVO.Item item=new MenuRespVO.Item();item.setId(1L);item.setName("经典拿铁");item.setNameEn("Caffe Latte");item.setPrice(1500);item.setImageUrl("/static/menu/latte.jpg");item.setEnabled(true);item.setSoldOut(false);
        var temperature=new MenuRespVO.Group();temperature.setId(1L);temperature.setName("温度");temperature.setNameEn("Temperature");
        temperature.setOptions(List.of(option(1,"热",0),option(2,"冰",200)));
        var sugar=new MenuRespVO.Group();sugar.setId(2L);sugar.setName("糖度");sugar.setNameEn("Sugar");sugar.setOptions(List.of(option(4,"半糖",100),option(5,"标准",0)));
        item.setOptionGroups(List.of(temperature,sugar));menu.setItems(List.of(item));menu.setCategories(List.of());return menu;
    }
    public static OrderCreateReqVO request(int quantity,Long...ids){
        var request=new OrderCreateReqVO();var item=new OrderCreateReqVO.Item();item.setItemId(1L);item.setQuantity(quantity);item.setOptionIds(List.of(ids));request.setItems(List.of(item));return request;
    }
    private static MenuRespVO.Option option(long id,String name,int price){var option=new MenuRespVO.Option();option.setId(id);option.setName(name);option.setNameEn(name);option.setPriceDelta(price);return option;}
}
