package cn.iocoder.yudao.module.cafe;

import cn.iocoder.yudao.module.cafe.service.card.MockStudentCardClient;
import cn.iocoder.yudao.module.cafe.service.card.StudentCardClient;
import net.jqwik.api.*;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 学生卡扣款/退款的属性测试。
 *
 * 余额守恒是这个系统最不能破的规矩：任何交错的扣款、退款序列结束后，
 * 余额必须等于 初始 − Σ首次成功扣款 + Σ对成功扣款的退款，一分钱都不能多出来或消失。
 * 幂等和退款屏障（退过款的单号永远不能再扣）也在整个输入域上断言。
 */
class StudentCardPropertyTest {

    private static final int INITIAL = 50000;

    /** 任意操作序列后，余额守恒且永不为负。 */
    @Property void balanceConserved(@ForAll("sequences") List<Op> ops) {
        MockStudentCardClient card = new MockStudentCardClient(INITIAL);
        Model model = new Model();
        for (Op op : ops) {
            if (op.debit()) {
                StudentCardClient.DebitResult got = card.debit("S1", op.amount(), op.orderNo());
                assertEquals(model.debit(op.amount(), op.orderNo()), got, "debit 结果与模型不一致: " + op);
            } else {
                card.refund("S1", op.amount(), op.orderNo());
                model.refund(op.amount(), op.orderNo());
            }
            assertEquals(model.balance, card.balance("S1"), "余额不守恒: 第 " + op + " 步后");
            assertTrue(card.balance("S1") >= 0, "余额为负: " + op);
        }
    }

    /** 同一幂等号重复扣款，余额只动一次（幂等性质）。 */
    @Property void repeatedDebitChargesOnce(@ForAll("amounts") int amount, @ForAll("repeat") int times) {
        MockStudentCardClient card = new MockStudentCardClient(INITIAL);
        StudentCardClient.DebitResult first = card.debit("S1", amount, "K1");
        int afterFirst = card.balance("S1");
        for (int i = 0; i < times; i++) assertEquals(first, card.debit("S1", amount, "K1"));
        assertEquals(afterFirst, card.balance("S1"));
    }

    /** 退过款的单号永远不能再扣（退款屏障），即使退款先于扣款到达。 */
    @Property void refundFencesLateDebit(@ForAll("amounts") int amount) {
        MockStudentCardClient card = new MockStudentCardClient(INITIAL);
        card.refund("S1", amount, "K2");
        assertEquals(StudentCardClient.DebitResult.DECLINED, card.debit("S1", amount, "K2"));
        assertEquals(INITIAL, card.balance("S1"));
    }

    /** 负数金额必须抛异常，绝不能当 0 处理。 */
    @Property void negativeAmountsThrow(@ForAll("negatives") int amount) {
        MockStudentCardClient card = new MockStudentCardClient(INITIAL);
        assertThrows(IllegalArgumentException.class, () -> card.debit("S1", amount, "K3"));
        assertThrows(IllegalArgumentException.class, () -> card.refund("S1", amount, "K3"));
        assertEquals(INITIAL, card.balance("S1"));
    }

    // --- 生成器与模型 -----------------------------------------------------

    /** 一步操作：debit=true 扣款，false 退款；金额与单号保持一致（幂等号重复时金额不变）。 */
    record Op(boolean debit, String orderNo, int amount) {}

    @Provide Arbitrary<Integer> amounts() { return Arbitraries.integers().between(0, 20000); }

    @Provide Arbitrary<Integer> negatives() { return Arbitraries.integers().between(Integer.MIN_VALUE, -1); }

    @Provide Arbitrary<Integer> repeat() { return Arbitraries.integers().between(1, 10); }

    @Provide Arbitrary<List<Op>> sequences() {
        // 同一单号的金额固定：先为每个单号定一个金额，再映射到操作序列
        return Arbitraries.integers().between(0, 20000).list().ofSize(4).flatMap(amountTable -> {
            Map<String, Integer> byOrder = Map.of("A", amountTable.get(0), "B", amountTable.get(1),
                    "C", amountTable.get(2), "D", amountTable.get(3));
            return Combinators.combine(Arbitraries.of(true, false), Arbitraries.of("A", "B", "C", "D"))
                    .as((debit, orderNo) -> new Op(debit, orderNo, byOrder.get(orderNo)))
                    .list().ofMinSize(0).ofMaxSize(40);
        });
    }

    /** 参照模型：接口注释里承诺的行为，独立实现一遍当 oracle。 */
    private static final class Model {
        int balance = INITIAL;
        /** orderNo → 首次扣款是否成功。 */
        final Map<String, Boolean> debited = new HashMap<>();
        final Set<String> refunded = new HashSet<>();

        StudentCardClient.DebitResult debit(int amount, String orderNo) {
            if (refunded.contains(orderNo)) return StudentCardClient.DebitResult.DECLINED;
            Boolean first = debited.get(orderNo);
            if (first != null) return first ? StudentCardClient.DebitResult.SUCCESS : StudentCardClient.DebitResult.DECLINED;
            boolean success = balance >= amount;
            if (success) balance -= amount;
            debited.put(orderNo, success);
            return success ? StudentCardClient.DebitResult.SUCCESS : StudentCardClient.DebitResult.DECLINED;
        }

        void refund(int amount, String orderNo) {
            if (refunded.contains(orderNo)) return;
            if (Boolean.TRUE.equals(debited.get(orderNo))) balance += amount;
            refunded.add(orderNo);
        }
    }
}
