package cn.iocoder.yudao.module.cafe;
import cn.iocoder.yudao.module.cafe.service.order.OrderPricing;
import cn.iocoder.yudao.framework.common.exception.ServiceException;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static cn.iocoder.yudao.module.cafe.CafeTestData.*;
class OrderPricingTest {
    @Test void calculatesServerPriceAndSnapshots(){var quote=OrderPricing.calculate(request(2,2L,4L),menu().getItems(),10);assertEquals(3600,quote.totalPrice());assertEquals(2,quote.cupCount());assertEquals("冰 / 半糖",quote.items().get(0).getOptionsText());assertEquals(1800,quote.items().get(0).getUnitPrice());assertEquals("温度",quote.items().get(0).getOptions().get(0).getGroupName());}
    @Test void rejectsOptionsFromOtherGroupsOrRepeatedSelections(){for(var ids:java.util.List.of(new Long[]{1L},new Long[]{1L,2L},new Long[]{1L,1L},new Long[]{1L,999L})){assertThrows(ServiceException.class,()->OrderPricing.calculate(request(1,ids),menu().getItems(),10));}}
    @Test void rejectsSoldOutDisabledMissingAndOverLimit(){var menu=menu();menu.getItems().get(0).setSoldOut(true);assertThrows(ServiceException.class,()->OrderPricing.calculate(request(1,1L,5L),menu.getItems(),10));menu.getItems().get(0).setSoldOut(false);menu.getItems().get(0).setEnabled(false);assertThrows(ServiceException.class,()->OrderPricing.calculate(request(1,1L,5L),menu.getItems(),10));assertThrows(ServiceException.class,()->OrderPricing.calculate(request(11,1L,5L),menu().getItems(),10));}
    @Test void bakeryRequiresNoOptions(){var menu=menu();menu.getItems().get(0).setOptionGroups(java.util.List.of());assertEquals(1500,OrderPricing.calculate(request(1),menu.getItems(),10).totalPrice());assertThrows(ServiceException.class,()->OrderPricing.calculate(request(1,1L),menu.getItems(),10));}
}
