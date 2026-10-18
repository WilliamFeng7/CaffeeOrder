package cn.iocoder.yudao.module.cafe.service.card;
import java.util.*;
/** 仅开发使用；进程重启后余额重置。每个幂等号同时记录扣款和冲正屏障。 */
public class MockStudentCardClient implements StudentCardClient {
    private final int initialBalance;
    private final Map<String,Integer> balances = new HashMap<>();
    private final Map<String,Entry> entries = new HashMap<>();
    private record Entry(String studentNo,int amount,DebitResult result,boolean refunded) {}
    public MockStudentCardClient(int initialBalance){this.initialBalance=initialBalance;}
    public synchronized int balance(String studentNo){return balances.computeIfAbsent(studentNo,k->initialBalance);}
    public synchronized DebitResult debit(String studentNo,int amount,String orderNo){
        validateAmount(amount);
        Entry old=entries.get(orderNo);
        if(old!=null){validateIdentity(old,studentNo,amount);return old.refunded()?DebitResult.DECLINED:old.result();}
        int balance=balance(studentNo);
        DebitResult result=balance>=amount?DebitResult.SUCCESS:DebitResult.DECLINED;
        if(result==DebitResult.SUCCESS)balances.put(studentNo,balance-amount);
        entries.put(orderNo,new Entry(studentNo,amount,result,false));
        return result;
    }
    public synchronized void refund(String studentNo,int amount,String orderNo){
        validateAmount(amount);
        Entry old=entries.get(orderNo);
        if(old!=null){
            validateIdentity(old,studentNo,amount);
            if(old.refunded())return;
            if(old.result()==DebitResult.SUCCESS)balances.put(studentNo,Math.addExact(balance(studentNo),amount));
        }
        entries.put(orderNo,new Entry(studentNo,amount,DebitResult.DECLINED,true));
    }
    private void validateIdentity(Entry entry,String studentNo,int amount){
        if(!entry.studentNo().equals(studentNo)||entry.amount()!=amount)throw new IllegalArgumentException("学生卡幂等号重复且金额或学号不同");
    }
    private void validateAmount(int amount){if(amount<0)throw new IllegalArgumentException("金额不能为负数");}
}
