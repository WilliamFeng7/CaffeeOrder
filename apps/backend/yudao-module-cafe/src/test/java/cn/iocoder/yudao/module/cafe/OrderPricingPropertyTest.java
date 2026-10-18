package cn.iocoder.yudao.module.cafe;

import cn.iocoder.yudao.module.cafe.controller.app.menu.vo.MenuRespVO;
import cn.iocoder.yudao.module.cafe.controller.app.order.vo.OrderCreateReqVO;
import cn.iocoder.yudao.module.cafe.service.order.OrderPricing;
import net.jqwik.api.*;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 定价的属性测试（property-based-testing：断言整条输入域上的规则，让生成器找反例）。
 *
 * 金额（分）和杯数是这个系统最不能算错的两个数，所以不为它们挑例子，
 * 而是让 jqwik 随机生成菜单和订单，核对总价永远等于逐项独立求和、杯数永远等于数量之和、
 * 以及任何输入都不可能算出负数或静默溢出。
 */
class OrderPricingPropertyTest {

    private static final int MAX_CUPS = 10;

    /** 总价 = Σ(单价×数量)，独立重算一遍对比（oracle 性质）。 */
    @Property void totalEqualsIndependentSum(@ForAll("cases") PricingCase c) {
        OrderPricing.Quote quote = OrderPricing.calculate(c.request(), c.menu().getItems(), MAX_CUPS);
        int expected = 0;
        for (OrderCreateReqVO.Item line : c.request().getItems()) {
            expected += unitPrice(c.menu(), line) * line.getQuantity();
        }
        assertEquals(expected, quote.totalPrice());
        assertEquals(expected, quote.items().stream().mapToInt(i -> i.getUnitPrice() * i.getQuantity()).sum());
    }

    /** 杯数 = Σ数量，一分钱一杯都不许错。 */
    @Property void cupCountEqualsQuantitySum(@ForAll("cases") PricingCase c) {
        OrderPricing.Quote quote = OrderPricing.calculate(c.request(), c.menu().getItems(), MAX_CUPS);
        assertEquals(c.request().getItems().stream().mapToInt(OrderCreateReqVO.Item::getQuantity).sum(), quote.cupCount());
    }

    /** 任何合法输入都不能算出负数，快照单价也不能为负。 */
    @Property void neverNegative(@ForAll("cases") PricingCase c) {
        OrderPricing.Quote quote = OrderPricing.calculate(c.request(), c.menu().getItems(), MAX_CUPS);
        assertTrue(quote.totalPrice() >= 0 && quote.cupCount() > 0);
        quote.items().forEach(item -> assertTrue(item.getUnitPrice() >= 0));
    }

    /** 订单里商品的排列顺序不影响金额（交换律）。 */
    @Property void itemOrderIrrelevant(@ForAll("cases") PricingCase c) {
        List<OrderCreateReqVO.Item> shuffled = new ArrayList<>(c.request().getItems());
        Collections.shuffle(shuffled, new Random(42));
        OrderCreateReqVO reordered = new OrderCreateReqVO();
        reordered.setItems(shuffled);
        assertEquals(
                OrderPricing.calculate(c.request(), c.menu().getItems(), MAX_CUPS).totalPrice(),
                OrderPricing.calculate(reordered, c.menu().getItems(), MAX_CUPS).totalPrice());
    }

    /** 超过杯数上限的订单必须被拒绝，而不是截断或算出一个价。 */
    @Property void overMaxCupsAlwaysThrows(@ForAll("bigOrders") OrderCreateReqVO request) {
        assertThrows(Exception.class, () -> OrderPricing.calculate(request, CafeTestData.menu().getItems(), MAX_CUPS));
    }

    /** 天文数字的数量只能抛异常，绝不能溢出成负数或绕回小数字。 */
    @Property void extremeQuantitiesNeverWrap(@ForAll("extremeOrders") OrderCreateReqVO request) {
        assertThrows(Exception.class, () -> OrderPricing.calculate(request, CafeTestData.menu().getItems(), Integer.MAX_VALUE));
    }

    /** 菜单价格、数量、加价全零的边界：总价为零但不是异常。 */
    @Property void freeOrderIsZeroNotError(@ForAll("freeCases") PricingCase c) {
        assertEquals(0, OrderPricing.calculate(c.request(), c.menu().getItems(), MAX_CUPS).totalPrice());
    }

    // --- 生成器 -----------------------------------------------------------

    /** 一次定价需要的全部输入：菜单 + 合法请求。 */
    record PricingCase(MenuRespVO menu, OrderCreateReqVO request) {}

    @Provide Arbitrary<PricingCase> cases() {
        return menus(0, 20000, 1000).flatMap(menu -> validRequests(menu).map(req -> new PricingCase(menu, req)));
    }

    @Provide Arbitrary<PricingCase> freeCases() {
        return menus(0, 0, 0).flatMap(menu -> validRequests(menu).map(req -> new PricingCase(menu, req)));
    }

    @Provide Arbitrary<OrderCreateReqVO> bigOrders() {
        return Arbitraries.integers().between(MAX_CUPS + 1, MAX_CUPS * 3)
                .map(qty -> CafeTestData.request(qty, 1L, 4L));
    }

    @Provide Arbitrary<OrderCreateReqVO> extremeOrders() {
        return Arbitraries.of(Integer.MAX_VALUE, Integer.MAX_VALUE - 1, 1_000_000_000)
                .map(qty -> CafeTestData.request(qty, 1L, 4L));
    }

    /** 随机菜单：1–6 个商品，价格 min–max 分；每个商品 0–2 个规格组，每组 1–4 个选项，加价 0–maxDelta 分。 */
    private static Arbitrary<MenuRespVO> menus(int minPrice, int maxPrice, int maxDelta) {
        return Arbitraries.integers().between(1, 6).flatMap(count -> {
            Arbitrary<MenuRespVO.Item> item = Combinators.combine(
                    Arbitraries.longs().between(1, 1000),
                    Arbitraries.integers().between(minPrice, maxPrice),
                    groups(maxDelta)
            ).as((id, price, groups) -> {
                MenuRespVO.Item it = new MenuRespVO.Item();
                it.setId(id); it.setName("商品" + id); it.setNameEn("Item" + id);
                it.setPrice(price); it.setImageUrl("/static/menu/x.jpg");
                it.setEnabled(true); it.setSoldOut(false); it.setOptionGroups(groups);
                return it;
            });
            return item.list().ofSize(count).map(items -> {
                // 商品 id 必须唯一，否则按 id 取商品时会串
                for (int i = 0; i < items.size(); i++) items.get(i).setId((long) i + 1);
                MenuRespVO menu = new MenuRespVO();
                menu.setItems(items); menu.setCategories(List.of());
                return menu;
            });
        });
    }

    private static Arbitrary<List<MenuRespVO.Group>> groups(int maxDelta) {
        Arbitrary<MenuRespVO.Group> group = options(maxDelta).map(options -> {
            MenuRespVO.Group g = new MenuRespVO.Group();
            g.setId(1L); g.setName("组"); g.setNameEn("Group"); g.setOptions(options);
            return g;
        });
        return group.list().ofMinSize(0).ofMaxSize(2).map(list -> {
            // 组 id、选项 id 全局唯一，且不同组的选项 id 不重叠（定价按 id 匹配）
            long next = 1;
            for (int gi = 0; gi < list.size(); gi++) {
                list.get(gi).setId((long) gi + 1);
                for (MenuRespVO.Option o : list.get(gi).getOptions()) o.setId(next++);
            }
            return list;
        });
    }

    private static Arbitrary<List<MenuRespVO.Option>> options(int maxDelta) {
        Arbitrary<MenuRespVO.Option> option = Arbitraries.integers().between(0, maxDelta).map(delta -> {
            MenuRespVO.Option o = new MenuRespVO.Option();
            o.setId(0L); o.setName("项"); o.setNameEn("Option"); o.setPriceDelta(delta);
            return o;
        });
        return option.list().ofMinSize(1).ofMaxSize(4);
    }

    /** 合法请求：挑 1–5 个商品，每个数量 1–10（合计会被压到上限内），每个规格组恰好选一个选项。 */
    private static Arbitrary<OrderCreateReqVO> validRequests(MenuRespVO menu) {
        return Combinators.combine(
                Arbitraries.integers().between(1, Math.min(5, menu.getItems().size())),
                Arbitraries.integers().between(1, 3).list().ofSize(menu.getItems().size())
        ).as((take, quantities) -> {
            List<MenuRespVO.Item> pool = new ArrayList<>(menu.getItems());
            Collections.shuffle(pool, new Random(7));
            List<OrderCreateReqVO.Item> lines = new ArrayList<>();
            int cups = 0;
            for (int i = 0; i < take; i++) {
                MenuRespVO.Item item = pool.get(i);
                int qty = Math.min(quantities.get(i), Math.max(1, MAX_CUPS - cups));
                cups += qty;
                OrderCreateReqVO.Item line = new OrderCreateReqVO.Item();
                line.setItemId(item.getId()); line.setQuantity(qty);
                List<Long> optionIds = new ArrayList<>();
                for (MenuRespVO.Group g : item.getOptionGroups()) optionIds.add(g.getOptions().get(0).getId());
                line.setOptionIds(optionIds);
                lines.add(line);
                if (cups >= MAX_CUPS) break;
            }
            OrderCreateReqVO request = new OrderCreateReqVO();
            request.setItems(lines);
            return request;
        });
    }

    /** 独立重算一行的单价：商品价 + 所选选项加价（oracle，不调用被测代码）。 */
    private static int unitPrice(MenuRespVO menu, OrderCreateReqVO.Item line) {
        MenuRespVO.Item item = menu.getItems().stream().filter(i -> i.getId().equals(line.getItemId())).findFirst().orElseThrow();
        int unit = item.getPrice();
        for (MenuRespVO.Group g : item.getOptionGroups()) {
            for (MenuRespVO.Option o : g.getOptions()) {
                if (line.getOptionIds().contains(o.getId())) unit += o.getPriceDelta();
            }
        }
        return unit;
    }
}
