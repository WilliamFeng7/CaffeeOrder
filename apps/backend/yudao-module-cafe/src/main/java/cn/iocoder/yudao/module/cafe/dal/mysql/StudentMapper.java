package cn.iocoder.yudao.module.cafe.dal.mysql;
import cn.iocoder.yudao.framework.mybatis.core.mapper.BaseMapperX;
import cn.iocoder.yudao.module.cafe.dal.dataobject.StudentDO;
import org.apache.ibatis.annotations.*;
@Mapper public interface StudentMapper extends BaseMapperX<StudentDO> {
    @Select("SELECT * FROM cafe_student WHERE id=#{id} AND deleted=0 FOR UPDATE")
    StudentDO lockById(@Param("id") Long id);
}
