package cn.iocoder.yudao.module.cafe.controller.admin.order;
import cn.iocoder.yudao.framework.common.pojo.*;
import cn.iocoder.yudao.framework.excel.core.util.ExcelUtils;
import cn.iocoder.yudao.module.cafe.controller.admin.order.vo.*;
import cn.iocoder.yudao.module.cafe.service.order.OrderQueryService;
import cn.iocoder.yudao.module.cafe.enums.OrderStatusEnum;
import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
@RestController @RequestMapping("/cafe/order") public class OrderController {
    @Resource private OrderQueryService query;
    @GetMapping("/page") @PreAuthorize("@ss.hasPermission('cafe:order:query')") public CommonResult<PageResult<AdminOrderRespVO>> page(@Valid OrderPageReqVO page){return success(query.adminPage(page));}
    @GetMapping("/get") @PreAuthorize("@ss.hasPermission('cafe:order:query')") public CommonResult<AdminOrderRespVO> get(@RequestParam("id") Long id){return success(query.adminDetail(id));}
    @GetMapping("/statistics") @PreAuthorize("@ss.hasPermission('cafe:order:query')") public CommonResult<Map<String,Long>> statistics(@Valid OrderPageReqVO page){return success(query.statistics(page));}
    @GetMapping("/export-excel") @PreAuthorize("@ss.hasPermission('cafe:order:export')") public void export(@Valid OrderPageReqVO page,HttpServletResponse response) throws Exception {
        page.setPageSize(PageParam.PAGE_SIZE_NONE);
        var values=query.adminPage(page).getList().stream().map(order->{
            OrderExcelVO row=new OrderExcelVO();row.setOrderNo(order.getOrderNo());row.setStatusName(OrderStatusEnum.nameOf(order.getStatus()));
            row.setStudentNo(order.getStudentNo());row.setStudentName(order.getStudentName());row.setPosOrderNo(order.getPosOrderNo());row.setTotalPrice(order.getTotalPrice());row.setCupCount(order.getCupCount());
            row.setCreateTime(format(order.getCreateTime()));row.setEnteredTime(format(order.getEnteredTime()));row.setDoneTime(format(order.getDoneTime()));row.setFailureReason(order.getFailureReason());
            row.setItems(order.getItems().stream().map(item->item.getName()+" × "+item.getQuantity()+(item.getOptionsText().isBlank()?"":"（"+item.getOptionsText()+"）")).collect(Collectors.joining("；")));return row;
        }).toList();
        ExcelUtils.write(response,"App订单.xlsx","App订单",OrderExcelVO.class,values);
    }
    private String format(LocalDateTime time){return time==null?"":time.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));}
}
