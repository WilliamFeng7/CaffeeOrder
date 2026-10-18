package cn.iocoder.yudao.module.cafe.service.shop;
import cn.iocoder.yudao.module.cafe.controller.admin.menu.vo.ShopSaveReqVO;
import cn.iocoder.yudao.module.cafe.dal.dataobject.ShopDO;
import cn.iocoder.yudao.module.cafe.dal.mysql.ShopMapper;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;
import java.time.*;
import java.util.*;
@Service public class ShopServiceImpl implements ShopService {
    @Resource private ShopMapper mapper;
    @Resource private Clock cafeClock;
    public ShopDO getShop(){return Objects.requireNonNull(mapper.selectById(1L),"请先执行数据库迁移");}
    public boolean canOrder(){return isOpen(getShop(),LocalTime.now(cafeClock));}
    /** 区间为 [start,end)，全部使用北京时间；24:00 表示当天结束，不支持跨午夜。 */
    public static boolean isOpen(ShopDO shop,LocalTime time){
        return Boolean.TRUE.equals(shop.getOpen())&&shop.getBusinessHours().stream().anyMatch(hour->
                !time.isBefore(parseTime(hour.getStart()))&&time.isBefore(parseTime(hour.getEnd())));
    }
    public void update(ShopSaveReqVO request){
        List<ShopDO.BusinessHour> hours=request.getBusinessHours().stream().map(h->new ShopDO.BusinessHour(h.getStart(),h.getEnd()))
            .sorted(Comparator.comparing(ShopDO.BusinessHour::getStart)).toList();
        for(int i=0;i<hours.size();i++){
            var hour=hours.get(i);
            if(hour.getStart().compareTo(hour.getEnd())>=0)throw new IllegalArgumentException("营业时段的结束时间必须晚于开始时间");
            if(i>0&&hours.get(i-1).getEnd().compareTo(hour.getStart())>0)throw new IllegalArgumentException("营业时段不能重叠");
        }
        ShopDO row=new ShopDO();row.setId(1L);row.setOpen(request.getOpen());row.setBanner(Objects.requireNonNullElse(request.getBanner(),""));row.setBusinessHours(hours);mapper.updateById(row);
    }
    private static LocalTime parseTime(String value){
        return "24:00".equals(value)?LocalTime.MAX:LocalTime.parse(value);
    }
}
