package cn.iocoder.yudao.module.cafe;
import cn.iocoder.yudao.module.cafe.service.card.*;
import org.junit.jupiter.api.Test;
import java.util.concurrent.*;
import static org.junit.jupiter.api.Assertions.*;
import static cn.iocoder.yudao.module.cafe.service.card.StudentCardClient.DebitResult.*;
class MockStudentCardClientTest {
    @Test void repeatsDebitRefundAndFencesLateDebit(){var card=new MockStudentCardClient(50000);assertEquals(SUCCESS,card.debit("S1",1500,"C1"));assertEquals(SUCCESS,card.debit("S1",1500,"C1"));assertEquals(48500,card.balance("S1"));card.refund("S1",1500,"C1");card.refund("S1",1500,"C1");assertEquals(50000,card.balance("S1"));assertEquals(DECLINED,card.debit("S1",1500,"C1"));card.refund("S1",1500,"C2");assertEquals(DECLINED,card.debit("S1",1500,"C2"));assertEquals(50000,card.balance("S1"));assertThrows(IllegalArgumentException.class,()->card.debit("S2",1500,"C1"));}
    @Test void concurrentDebitCannotOverdraw() throws Exception {var card=new MockStudentCardClient(100);try(var pool=Executors.newFixedThreadPool(8)){var tasks=java.util.stream.IntStream.range(0,20).mapToObj(i->(Callable<StudentCardClient.DebitResult>)()->card.debit("S1",100,"C"+i)).toList();long success=0;for(var future:pool.invokeAll(tasks))if(future.get()==SUCCESS)success++;assertEquals(1,success);assertEquals(0,card.balance("S1"));}}
    @Test void mismatchedIdentityCannotMoveBalance() {
        var card=new MockStudentCardClient(50000);
        assertEquals(SUCCESS,card.debit("S1",1500,"C1"));
        assertThrows(IllegalArgumentException.class,()->card.debit("S1",1600,"C1"));
        assertThrows(IllegalArgumentException.class,()->card.refund("S2",1500,"C1"));
        assertThrows(IllegalArgumentException.class,()->card.refund("S1",1600,"C1"));
        assertEquals(48500,card.balance("S1"));
        card.refund("S1",1500,"C1");
        assertEquals(50000,card.balance("S1"));
    }

    @Test void concurrentRefundRestoresExactlyOnce() throws Exception {
        var card=new MockStudentCardClient(100);
        try(var pool=Executors.newFixedThreadPool(8)){
            var debits=java.util.stream.IntStream.range(0,20).mapToObj(i->(Callable<StudentCardClient.DebitResult>)()->card.debit("S1",100,"C"+i)).toList();
            String successfulOrder=null;
            var results=pool.invokeAll(debits);
            for(int i=0;i<results.size();i++)if(results.get(i).get()==SUCCESS){successfulOrder="C"+i;break;}
            assertNotNull(successfulOrder);
            final String orderNo=successfulOrder;
            var refunds=java.util.stream.IntStream.range(0,20).mapToObj(i->(Callable<Void>)()->{card.refund("S1",100,orderNo);return null;}).toList();
            for(var future:pool.invokeAll(refunds))future.get();
        }
        assertEquals(100,card.balance("S1"));
    }
}
