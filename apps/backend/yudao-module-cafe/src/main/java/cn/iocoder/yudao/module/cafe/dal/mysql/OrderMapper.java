package cn.iocoder.yudao.module.cafe.dal.mysql;
import cn.iocoder.yudao.framework.mybatis.core.mapper.BaseMapperX;
import cn.iocoder.yudao.module.cafe.dal.dataobject.OrderDO;
import org.apache.ibatis.annotations.*;
import java.time.LocalDateTime;
@Mapper public interface OrderMapper extends BaseMapperX<OrderDO> {
    @Update("UPDATE cafe_order SET status=#{next},version=version+1,update_time=#{now},failure_reason=#{reason},retry_after=#{retryAfter} " +
            "WHERE id=#{id} AND status=#{expected} AND version=#{version} AND deleted=0")
    int changePayment(@Param("id") Long id,@Param("expected") int expected,@Param("version") int version,
                      @Param("next") int next,@Param("reason") String reason,@Param("retryAfter") LocalDateTime retryAfter,@Param("now") LocalDateTime now);
    @Update("UPDATE cafe_order SET status=20,pos_order_no=#{pos},entered_time=COALESCE(entered_time,#{now}),version=version+1,update_time=#{now} " +
            "WHERE id=#{id} AND status=#{expected} AND version=#{version} AND deleted=0")
    int enter(@Param("id") Long id,@Param("expected") int expected,@Param("version") int version,@Param("pos") String pos,@Param("now") LocalDateTime now);
    @Update("UPDATE cafe_order SET status=#{next},done_time=#{doneTime},version=version+1,update_time=#{now} " +
            "WHERE id=#{id} AND status=#{expected} AND version=#{version} AND deleted=0")
    int changeState(@Param("id") Long id,@Param("expected") int expected,@Param("version") int version,
                    @Param("next") int next,@Param("doneTime") LocalDateTime doneTime,@Param("now") LocalDateTime now);
}
