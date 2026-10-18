package cn.iocoder.yudao.module.cafe.enums;
import lombok.Getter;
@Getter
public enum OrderStatusEnum {
    PAYING(0,"支付中"), FAILED(1,"支付失败"), COMPENSATING(2,"支付中（补偿中）"),
    WAITING(10,"待录单"), MAKING(20,"制作中"), DONE(30,"制作完成");
    private final int status; private final String name;
    OrderStatusEnum(int status,String name){ this.status=status; this.name=name; }
    public static String nameOf(int status){for(var value:values())if(value.status==status)return value.name;return "未知状态";}
    public static boolean visible(int status){return status==10||status==20||status==30;}
}
