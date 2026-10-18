package cn.iocoder.yudao.module.cafe.enums;
import cn.iocoder.yudao.framework.common.exception.ErrorCode;
public interface ErrorCodeConstants {
    ErrorCode SHOP_CLOSED = new ErrorCode(1_080_001_001, "当前不在营业时段，暂时不能下单");
    ErrorCode MENU_INVALID = new ErrorCode(1_080_002_001, "商品或规格已变化，请重新选择");
    ErrorCode MENU_UNAVAILABLE = new ErrorCode(1_080_002_002, "商品已下架或售罄，请重新选择");
    ErrorCode MENU_NOT_FOUND = new ErrorCode(1_080_002_003, "分类、商品或规格组不存在，请刷新");
    ErrorCode MENU_IN_USE = new ErrorCode(1_080_002_004, "仍有商品使用这个分类或规格组，请先调整商品");
    ErrorCode MENU_DUPLICATE = new ErrorCode(1_080_002_005, "分类编码或选项重复，请检查");
    ErrorCode CUPS_LIMIT = new ErrorCode(1_080_003_001, "每单最多 {} 杯，请调整数量");
    ErrorCode CARD_UNAVAILABLE = new ErrorCode(1_080_003_006, "学生卡余额暂时无法查询，请稍后重试");
    ErrorCode CARD_DECLINED = new ErrorCode(1_080_003_002, "学生卡余额不足或扣款被拒绝");
    ErrorCode PAYMENT_UNKNOWN = new ErrorCode(1_080_003_003, "扣款结果暂时无法确认，系统正在处理，请稍后查看余额");
    ErrorCode ORDER_PAYING = new ErrorCode(1_080_003_004, "订单正在支付，请稍后查看订单");
    ErrorCode REQUEST_CONFLICT = new ErrorCode(1_080_003_005, "重复请求的商品不同，请重新下单");
    ErrorCode ORDER_REFUNDED = new ErrorCode(1_080_003_007, "扣款已确认退回，可以重新下单");
    ErrorCode ORDER_NOT_FOUND = new ErrorCode(1_080_004_001, "App 订单不存在，请刷新");
    ErrorCode ORDER_CHANGED = new ErrorCode(1_080_004_002, "订单状态已变化，请刷新");
    ErrorCode POS_DUPLICATE = new ErrorCode(1_080_004_003, "当天已使用这个收银单号，请检查");
    ErrorCode ORDER_NOT_TODAY = new ErrorCode(1_080_004_004, "只能操作当天的 App 订单");
    ErrorCode AUTH_FAILED = new ErrorCode(1_080_005_001, "钉钉免登失败，请重新打开学生端");
    ErrorCode STUDENT_NO_MISSING = new ErrorCode(1_080_005_002, "钉钉通讯录未配置学号，请联系学校管理员");
    ErrorCode STUDENT_NOT_FOUND = new ErrorCode(1_080_005_003, "学生登录已失效，请重新打开学生端");
    ErrorCode STUDENT_CONFLICT = new ErrorCode(1_080_005_004, "学号已关联其他钉钉账号，请联系学校管理员");
    ErrorCode STUDENT_CREDENTIALS_INVALID = new ErrorCode(1_080_005_005, "学号或密码错误");
    ErrorCode STUDENT_LOGIN_RATE_LIMITED = new ErrorCode(1_080_005_006, "登录尝试过于频繁，请稍后再试");
    ErrorCode DEV_LOGIN_UNAUTHORIZED = new ErrorCode(1_080_005_007, "开发登录已禁用或凭证无效");
}
