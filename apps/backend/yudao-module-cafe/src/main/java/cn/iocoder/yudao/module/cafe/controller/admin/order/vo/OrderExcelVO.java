package cn.iocoder.yudao.module.cafe.controller.admin.order.vo;
import cn.idev.excel.annotation.ExcelProperty;
import cn.idev.excel.annotation.ExcelIgnoreUnannotated;
import lombok.Data;
@Data @ExcelIgnoreUnannotated public class OrderExcelVO {
    @ExcelProperty("App 订单号") private String orderNo;
    @ExcelProperty("状态") private String statusName;
    @ExcelProperty("学号") private String studentNo;
    @ExcelProperty("姓名") private String studentName;
    @ExcelProperty("收银单号") private String posOrderNo;
    @ExcelProperty("订单金额（分）") private Integer totalPrice;
    @ExcelProperty("杯数") private Integer cupCount;
    @ExcelProperty("下单时间（北京时间）") private String createTime;
    @ExcelProperty("回填时间（北京时间）") private String enteredTime;
    @ExcelProperty("制作完成时间（北京时间）") private String doneTime;
    @ExcelProperty("商品与规格") private String items;
    @ExcelProperty("支付说明") private String failureReason;
}
