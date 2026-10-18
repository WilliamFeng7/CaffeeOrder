package cn.iocoder.yudao.module.cafe;
import cn.iocoder.yudao.module.cafe.dal.dataobject.ShopDO;
import cn.iocoder.yudao.module.cafe.service.shop.ShopServiceImpl;
import org.junit.jupiter.api.Test;
import java.time.LocalTime;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;
class ShopServiceTest {
    @Test void checksBothIntervalsAndExclusiveEnd(){var shop=new ShopDO();shop.setOpen(true);shop.setBusinessHours(List.of(new ShopDO.BusinessHour("11:40","12:30"),new ShopDO.BusinessHour("15:30","17:00")));for(String time:List.of("11:40","12:29:59","15:30","16:59:59"))assertTrue(ShopServiceImpl.isOpen(shop,LocalTime.parse(time)),time);for(String time:List.of("00:00","11:39:59","12:30","15:29:59","17:00","23:59"))assertFalse(ShopServiceImpl.isOpen(shop,LocalTime.parse(time)),time);shop.setOpen(false);assertFalse(ShopServiceImpl.isOpen(shop,LocalTime.NOON));shop.setOpen(true);shop.setBusinessHours(List.of());assertFalse(ShopServiceImpl.isOpen(shop,LocalTime.NOON));}
    @Test void fullDayRemainsOpenDuringLastMinute(){var shop=new ShopDO();shop.setOpen(true);shop.setBusinessHours(List.of(new ShopDO.BusinessHour("00:00","24:00")));for(String time:List.of("00:00","12:00","23:59","23:59:59.999"))assertTrue(ShopServiceImpl.isOpen(shop,LocalTime.parse(time)),time);}
}
