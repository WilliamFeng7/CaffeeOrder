package cn.iocoder.yudao.module.cafe;
import cn.iocoder.yudao.module.cafe.dal.mysql.*;
import cn.iocoder.yudao.module.cafe.dal.dataobject.*;
import cn.iocoder.yudao.module.cafe.framework.CafeProperties;
import cn.iocoder.yudao.module.cafe.service.card.*;
import cn.iocoder.yudao.module.cafe.service.menu.MenuService;
import cn.iocoder.yudao.module.cafe.service.shop.ShopService;
import cn.iocoder.yudao.module.cafe.service.order.*;
import cn.iocoder.yudao.framework.common.pojo.PageParam;
import cn.iocoder.yudao.framework.common.exception.ServiceException;
import cn.iocoder.yudao.module.cafe.controller.admin.order.vo.OrderPageReqVO;
import com.baomidou.mybatisplus.spring.MybatisSqlSessionFactoryBean;
import com.baomidou.mybatisplus.core.config.GlobalConfig;
import com.baomidou.mybatisplus.annotation.IdType;
import jakarta.annotation.Resource;
import org.apache.ibatis.session.SqlSessionFactory;
import org.mybatis.spring.annotation.MapperScan;
import org.junit.jupiter.api.*;
import org.springframework.context.annotation.*;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.mockito.ArgumentMatchers.*;
import static cn.iocoder.yudao.module.cafe.CafeTestData.*;
import static cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.*;
import static cn.iocoder.yudao.module.cafe.service.card.StudentCardClient.DebitResult.*;
@SpringJUnitConfig(OrderLifecycleTest.Config.class)
class OrderLifecycleTest {
    @Configuration @MapperScan("cn.iocoder.yudao.module.cafe.dal.mysql") @Import({OrderServiceImpl.class,OrderQueryServiceImpl.class})
    static class Config {
        @Bean DataSource dataSource(){return new DriverManagerDataSource("jdbc:h2:mem:cafe;MODE=MySQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1","sa","");}
        @Bean SqlSessionFactory sqlSessionFactory(DataSource dataSource)throws Exception{var bean=new MybatisSqlSessionFactoryBean();bean.setDataSource(dataSource);var global=new GlobalConfig();global.setDbConfig(new GlobalConfig.DbConfig().setIdType(IdType.AUTO));bean.setGlobalConfig(global);var interceptor=new com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor();interceptor.addInnerInterceptor(new com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor(com.baomidou.mybatisplus.annotation.DbType.H2));bean.setPlugins(interceptor);return bean.getObject();}
        @Bean TransactionTemplate transactions(DataSource dataSource){return new TransactionTemplate(new DataSourceTransactionManager(dataSource));}
        @Bean MenuService menu(){return mock(MenuService.class);}
        @Bean ShopService shop(){return mock(ShopService.class);}
        @Bean StudentCardClient cards(){return mock(StudentCardClient.class);}
        @Bean CafeProperties properties(){return new CafeProperties();}
        @Bean MutableClock cafeClock(){return new MutableClock();}
    }
    static class MutableClock extends Clock {
        Instant instant=ZonedDateTime.of(2026,10,17,12,0,0,0,ZoneId.of("Asia/Shanghai")).toInstant();
        public ZoneId getZone(){return ZoneId.of("Asia/Shanghai");}
        public Clock withZone(ZoneId zone){return this;}
        public Instant instant(){return instant;}
        void advance(long seconds){instant=instant.plusSeconds(seconds);}
    }
    @Resource OrderService service; @Resource OrderQueryService query; @Resource OrderMapper orders;
    @Resource StudentCardClient cards; @Resource MenuService menu; @Resource ShopService shop;
    @Resource DataSource dataSource; @Resource MutableClock cafeClock;
    MockStudentCardClient ledger;
    @BeforeEach void prepare(){
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Shanghai"));
        new ResourceDatabasePopulator(new ClassPathResource("schema.sql")).execute(dataSource);
        cafeClock.instant=ZonedDateTime.of(2026,10,17,12,0,0,0,ZoneId.of("Asia/Shanghai")).toInstant();
        reset(cards,menu,shop);ledger=new MockStudentCardClient(50000);
        when(menu.getMenu(true)).thenReturn(CafeTestData.menu());when(shop.canOrder()).thenReturn(true);
        when(cards.debit(anyString(),anyInt(),anyString())).thenAnswer(i->ledger.debit(i.getArgument(0),i.getArgument(1),i.getArgument(2)));
        doAnswer(i->{ledger.refund(i.getArgument(0),i.getArgument(1),i.getArgument(2));return null;}).when(cards).refund(anyString(),anyInt(),anyString());
    }
    Long create(String key){return service.create(1L,request(1,1L,5L),key);}
    @Test void normalFlowCorrectionAndUndoPreserveSnapshot(){
        Long id=create("normal");assertEquals(48500,ledger.balance("S001"));assertEquals(1,query.waitingCount());assertEquals(1,query.board().get("waiting").size());
        var student=query.getStudentOrder(1L,id);assertEquals(0,student.getAheadCount());assertNull(student.getPosOrderNo());assertEquals(1500,student.getTotalPrice());
        service.enter(id,"  00017  ");assertEquals("00017",query.getStudentOrder(1L,id).getPosOrderNo());assertEquals(20,orders.selectById(id).getStatus());
        var entered=orders.selectById(id).getEnteredTime();service.enter(id,"00018");assertEquals(entered,orders.selectById(id).getEnteredTime());
        service.done(id);assertEquals(30,orders.selectById(id).getStatus());assertNotNull(orders.selectById(id).getDoneTime());assertEquals(0,query.waitingCount());assertThrows(ServiceException.class,()->service.done(id));
        service.undoDone(id);assertEquals(20,orders.selectById(id).getStatus());assertNull(orders.selectById(id).getDoneTime());assertThrows(ServiceException.class,()->query.getStudentOrder(2L,id));
        assertEquals("经典拿铁",query.getStudentOrder(1L,id).getItems().get(0).getName());
    }
    @Test void replayAndRapidDuplicateDebitOnlyOnce() throws Exception {
        try(var pool=Executors.newFixedThreadPool(8)){
            var futures=pool.invokeAll(java.util.stream.IntStream.range(0,8).mapToObj(i->(Callable<Long>)()->{try{return create("same");}catch(ServiceException e){assertEquals(ORDER_PAYING.getCode(),e.getCode());return null;}}).toList());
            Set<Long> ids=new HashSet<>();for(var future:futures){var id=future.get();if(id!=null)ids.add(id);}assertEquals(1,ids.size());
        }
        assertEquals(1,orders.selectCount());assertEquals(48500,ledger.balance("S001"));verify(cards,times(1)).debit(anyString(),anyInt(),anyString());
        assertThrows(ServiceException.class,()->service.create(1L,request(2,1L,5L),"same"));
        assertEquals(create("same"),service.create(1L,request(1,1L,5L),null));
    }
    @Test void declineIsHiddenAndDoesNotRefund(){when(cards.debit(anyString(),anyInt(),anyString())).thenReturn(DECLINED);assertEquals(CARD_DECLINED.getCode(),assertThrows(ServiceException.class,()->create("decline")).getCode());assertEquals(1,orders.selectList().get(0).getStatus());assertEquals(0,query.studentPage(1L,new PageParam()).getTotal());assertTrue(query.board().get("waiting").isEmpty());verify(cards,never()).refund(anyString(),anyInt(),anyString());}
    @Test void unknownDebitIsCompensated(){when(cards.debit(anyString(),anyInt(),anyString())).thenAnswer(i->{ledger.debit(i.getArgument(0),i.getArgument(1),i.getArgument(2));return UNKNOWN;});assertThrows(ServiceException.class,()->create("unknown"));assertEquals(50000,ledger.balance("S001"));assertEquals(1,orders.selectList().get(0).getStatus());assertEquals(0,query.waitingCount());verify(cards,times(1)).refund(anyString(),anyInt(),anyString());}
    @Test void refundFailureRemainsInternalAndIsRetried(){when(cards.debit(anyString(),anyInt(),anyString())).thenReturn(UNKNOWN);doThrow(new RuntimeException("timeout")).doNothing().when(cards).refund(anyString(),anyInt(),anyString());assertThrows(ServiceException.class,()->create("retry"));assertEquals(2,orders.selectList().get(0).getStatus());cafeClock.advance(61);service.recoverPayments();assertEquals(1,orders.selectList().get(0).getStatus());verify(cards,times(2)).refund(anyString(),anyInt(),anyString());}
    @Test void differentRequestKeyCannotOverlapUnresolvedPayment(){
        when(cards.debit(anyString(),anyInt(),anyString())).thenReturn(UNKNOWN);
        doThrow(new RuntimeException("timeout")).doNothing().when(cards).refund(anyString(),anyInt(),anyString());
        assertEquals(PAYMENT_UNKNOWN.getCode(),assertThrows(ServiceException.class,()->create("pending-first")).getCode());
        assertEquals(2,orders.selectList().get(0).getStatus());
        assertEquals(ORDER_PAYING.getCode(),assertThrows(ServiceException.class,()->service.create(1L,request(1,1L,5L),"pending-second")).getCode());
        assertEquals(1,orders.selectCount());verify(cards,times(1)).debit(anyString(),anyInt(),anyString());

        cafeClock.advance(61);service.recoverPayments();assertEquals(1,orders.selectList().get(0).getStatus());
        reset(cards);when(menu.getMenu(true)).thenReturn(CafeTestData.menu());when(shop.canOrder()).thenReturn(true);
        when(cards.debit(anyString(),anyInt(),anyString())).thenAnswer(i->ledger.debit(i.getArgument(0),i.getArgument(1),i.getArgument(2)));
        doAnswer(i->{ledger.refund(i.getArgument(0),i.getArgument(1),i.getArgument(2));return null;}).when(cards).refund(anyString(),anyInt(),anyString());
        Long accepted=service.create(1L,request(1,1L,5L),"pending-second");
        assertNotNull(accepted);assertEquals(2,orders.selectCount());assertEquals(48500,ledger.balance("S001"));
    }
    @Test void confirmedRefundReplayHasTerminalOutcome(){
        when(cards.debit(anyString(),anyInt(),anyString())).thenAnswer(i->{ledger.debit(i.getArgument(0),i.getArgument(1),i.getArgument(2));return UNKNOWN;});
        assertEquals(PAYMENT_UNKNOWN.getCode(),assertThrows(ServiceException.class,()->create("refunded")).getCode());
        assertEquals(50000,ledger.balance("S001"));
        assertEquals(ORDER_REFUNDED.getCode(),assertThrows(ServiceException.class,()->create("refunded")).getCode());
    }
    @Test void statisticsKeepOrderCountAndPaidAmountSemantics(){
        Long waiting=create("stats-waiting");
        Long finished=service.create(1L,request(2,1L,5L),"stats-finished");service.enter(finished,"S-2");service.done(finished);
        when(cards.debit(anyString(),anyInt(),anyString())).thenReturn(DECLINED);
        assertThrows(ServiceException.class,()->service.create(1L,request(1,1L,5L),"stats-declined"));

        var all=query.statistics(new OrderPageReqVO());
        assertEquals(3L,all.get("orderCount"));
        assertEquals(6000L,all.get("totalPrice"));
        assertEquals(4500L,all.get("paidAmount"));
        var failed=new OrderPageReqVO();failed.setStatus(1);
        assertEquals(Map.of("orderCount",1L,"totalPrice",1500L,"paidAmount",0L),query.statistics(failed));
        var todayFilter=new OrderPageReqVO();todayFilter.setStartDate(LocalDate.of(2026,10,17));todayFilter.setEndDate(LocalDate.of(2026,10,17));
        assertEquals(3L,query.statistics(todayFilter).get("orderCount"));
        assertNotNull(waiting);
    }
    @Test void recoveryHandlesCrashedProcessAndLateDebitCannotReviveOrder() throws Exception {
        CountDownLatch started=new CountDownLatch(1),finish=new CountDownLatch(1);
        when(cards.debit(anyString(),anyInt(),anyString())).thenAnswer(i->{started.countDown();assertTrue(finish.await(10,TimeUnit.SECONDS));return ledger.debit(i.getArgument(0),i.getArgument(1),i.getArgument(2));});
        try(var pool=Executors.newSingleThreadExecutor()){
            var future=pool.submit(()->assertThrows(ServiceException.class,()->create("slow")));
            assertTrue(started.await(5,TimeUnit.SECONDS));cafeClock.advance(181);service.recoverPayments();finish.countDown();future.get(10,TimeUnit.SECONDS);
        }
        assertEquals(1,orders.selectList().get(0).getStatus());assertEquals(50000,ledger.balance("S001"));assertEquals(0,query.waitingCount());
    }
    @Test void conditionalStateUpdateHasSingleWinner() throws Exception {
        Long id=create("race");service.enter(id,"A1");AtomicInteger success=new AtomicInteger();
        try(var pool=Executors.newFixedThreadPool(8)){var futures=pool.invokeAll(java.util.stream.IntStream.range(0,8).mapToObj(i->(Callable<Void>)()->{try{service.done(id);success.incrementAndGet();}catch(ServiceException ex){assertEquals(ORDER_CHANGED.getCode(),ex.getCode());}return null;}).toList());for(var future:futures)future.get();}
        assertEquals(1,success.get());assertEquals(30,orders.selectById(id).getStatus());
    }
    @Test void databasePreventsConcurrentSameDayPosDuplicates() throws Exception {
        Long a=create("pos-a"),b=create("pos-b");AtomicInteger success=new AtomicInteger();AtomicInteger duplicate=new AtomicInteger();
        try(var pool=Executors.newFixedThreadPool(2)){var futures=pool.invokeAll(List.of(a,b).stream().map(id->(Callable<Void>)()->{try{service.enter(id,"0001");success.incrementAndGet();}catch(ServiceException ex){assertEquals(POS_DUPLICATE.getCode(),ex.getCode());duplicate.incrementAndGet();}return null;}).toList());for(var future:futures)future.get();}
        assertEquals(1,success.get());assertEquals(1,duplicate.get());
    }
    @Test void queueAndAheadCountTrackOnlyActiveOrders(){
        Long first=create("queue-first"),second=create("queue-second");
        assertEquals(2,query.waitingCount());
        assertEquals(0,query.getStudentOrder(1L,first).getAheadCount());
        assertEquals(1,query.getStudentOrder(1L,second).getAheadCount());
        service.enter(first,"Q1");
        assertEquals(2,query.waitingCount());
        assertEquals(1,query.getStudentOrder(1L,second).getAheadCount());
        service.done(first);
        assertEquals(1,query.waitingCount());
        assertEquals(0,query.getStudentOrder(1L,second).getAheadCount());
    }
    @Test void naturalDayBoundaryControlsQueueAndUndo(){Long yesterday=create("day-1");service.enter(yesterday,"1");service.done(yesterday);cafeClock.advance(86400);Long today=create("day-2");service.enter(today,"1");assertEquals(1,query.waitingCount());assertThrows(ServiceException.class,()->service.undoDone(yesterday));assertNull(query.getStudentOrder(1L,yesterday).getAheadCount());}
    @Test void closedShopNeverCreatesDraftOrDebits(){when(shop.canOrder()).thenReturn(false);assertEquals(SHOP_CLOSED.getCode(),assertThrows(ServiceException.class,()->create("closed")).getCode());assertEquals(0,orders.selectCount());verifyNoInteractions(cards);}
}
