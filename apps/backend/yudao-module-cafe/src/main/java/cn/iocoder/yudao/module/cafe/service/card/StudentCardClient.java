package cn.iocoder.yudao.module.cafe.service.card;
/**
 * 学生卡边界，金额单位为分。真实实现必须满足以下约定：
 * debit 以 orderNo 幂等；refund 以同一个 orderNo 幂等，不能重复退回余额。
 * refund 成功必须阻止这个 orderNo 的迟到扣款（撤销/冲正屏障），即使退款先到也一样。
 * 网络错误或不确定的响应必须返回 UNKNOWN 或抛异常，绝不能伪装成明确拒绝。
 */
public interface StudentCardClient {
    enum DebitResult { SUCCESS, DECLINED, UNKNOWN }
    int balance(String studentNo);
    DebitResult debit(String studentNo, int amount, String orderNo);
    void refund(String studentNo, int amount, String orderNo);
}
