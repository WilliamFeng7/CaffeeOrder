package cn.iocoder.yudao.module.cafe.service.order;
import cn.iocoder.yudao.module.cafe.controller.app.menu.vo.MenuRespVO;
import cn.iocoder.yudao.module.cafe.controller.app.order.vo.OrderCreateReqVO;
import cn.iocoder.yudao.module.cafe.dal.dataobject.OrderItemDO;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.*;
/** 服务端价格与规格校验；不使用请求中的任何金额。 */
public final class OrderPricing {
    private OrderPricing() {}
    public record Quote(int totalPrice,int cupCount,List<OrderItemDO> items) {}
    public static Quote calculate(OrderCreateReqVO request,List<MenuRespVO.Item> menu,int maxCups){
        Map<Long,MenuRespVO.Item> byId=menu.stream().collect(Collectors.toMap(MenuRespVO.Item::getId,Function.identity()));
        int total=0,cups=0;List<OrderItemDO> snapshots=new ArrayList<>();
        for(var line:request.getItems()){
            if(line.getQuantity()==null||line.getQuantity()<1)throw exception(MENU_INVALID);
            cups=Math.addExact(cups,line.getQuantity());if(cups>maxCups)throw exception(CUPS_LIMIT,maxCups);
            MenuRespVO.Item item=byId.get(line.getItemId());
            if(item==null||!Boolean.TRUE.equals(item.getEnabled())||Boolean.TRUE.equals(item.getSoldOut()))throw exception(MENU_UNAVAILABLE);
            Set<Long> selected=new HashSet<>(line.getOptionIds());
            if(selected.size()!=line.getOptionIds().size()||selected.size()!=item.getOptionGroups().size())throw exception(MENU_INVALID);
            int unit=item.getPrice();List<OrderItemDO.OptionSnapshot> options=new ArrayList<>();
            for(var group:item.getOptionGroups()){
                var chosen=group.getOptions().stream().filter(option->selected.contains(option.getId())).toList();
                if(chosen.size()!=1)throw exception(MENU_INVALID);
                var option=chosen.get(0);selected.remove(option.getId());unit=Math.addExact(unit,option.getPriceDelta());
                options.add(new OrderItemDO.OptionSnapshot(group.getName(),group.getNameEn(),option.getName(),option.getNameEn()));
            }
            if(!selected.isEmpty()||unit<0)throw exception(MENU_INVALID);
            OrderItemDO snapshot=new OrderItemDO();snapshot.setItemId(item.getId());snapshot.setName(item.getName());snapshot.setNameEn(item.getNameEn());
            snapshot.setImageUrl(item.getImageUrl());snapshot.setUnitPrice(unit);snapshot.setQuantity(line.getQuantity());snapshot.setOptions(options);
            snapshot.setOptionsText(options.stream().map(OrderItemDO.OptionSnapshot::getName).collect(Collectors.joining(" / ")));
            snapshots.add(snapshot);total=Math.addExact(total,Math.multiplyExact(unit,line.getQuantity()));
        }
        if(cups==0)throw exception(MENU_INVALID);
        return new Quote(total,cups,List.copyOf(snapshots));
    }
}
