package cn.iocoder.yudao.module.cafe.service.auth;
import cn.iocoder.yudao.module.cafe.controller.app.auth.vo.AuthLoginRespVO;
import cn.iocoder.yudao.module.cafe.dal.dataobject.StudentDO;
import cn.iocoder.yudao.module.cafe.dal.mysql.StudentMapper;
import cn.iocoder.yudao.framework.common.enums.UserTypeEnum;
import cn.iocoder.yudao.module.system.service.oauth2.OAuth2TokenService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import jakarta.annotation.Resource;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import java.nio.charset.StandardCharsets;
import java.time.*;
import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.*;
@Service public class StudentAuthServiceImpl implements StudentAuthService {
    private static final String DUMMY_PASSWORD_HASH =
            "$2a$12$Tl0OE2N2084PwMsYABj85Oh.TSmhhBfZVDZ2.cVengSLT8MoBjvl.";
    @Resource private StudentMapper students;
    @Resource private DingTalkClient dingTalk;
    @Resource private OAuth2TokenService tokens;
    @Resource private Clock cafeClock;
    @Resource private PasswordEncoder passwordEncoder;
    @Resource private StudentLoginRateLimiter rateLimiter;
    public AuthLoginRespVO dingTalkLogin(String authCode){var user=dingTalk.identity(authCode);return login(user.studentNo(),user.name(),user.userId());}
    public AuthLoginRespVO passwordLogin(String studentNo,String password){
        rateLimiter.check(studentNo);
        if(password==null||password.getBytes(StandardCharsets.UTF_8).length>72)throw exception(STUDENT_CREDENTIALS_INVALID);
        StudentDO student=students.selectOne(new LambdaQueryWrapper<StudentDO>().eq(StudentDO::getStudentNo,studentNo));
        String hash=student==null||student.getPasswordHash()==null||student.getPasswordHash().isBlank()
                ? DUMMY_PASSWORD_HASH : student.getPasswordHash();
        boolean matches=passwordEncoder.matches(password,hash);
        if(student==null||student.getPasswordHash()==null||student.getPasswordHash().isBlank()||!matches){
            throw exception(STUDENT_CREDENTIALS_INVALID);
        }
        student.setLastLoginTime(LocalDateTime.now(cafeClock));
        if(students.updateById(student)!=1)throw exception(STUDENT_CREDENTIALS_INVALID);
        AuthLoginRespVO response=issueToken(student,student.getName());
        rateLimiter.reset(studentNo);
        return response;
    }
    public AuthLoginRespVO devLogin(String studentNo,String name){return login(studentNo,name,null);}
    public StudentDO getStudent(Long id){StudentDO student=students.selectById(id);if(student==null)throw exception(STUDENT_NOT_FOUND);return student;}
    private AuthLoginRespVO login(String studentNo,String name,String userId){
        LocalDateTime now=LocalDateTime.now(cafeClock);
        StudentDO student=students.selectOne(new LambdaQueryWrapper<StudentDO>().eq(StudentDO::getStudentNo,studentNo));
        if(student==null){
            student=new StudentDO();student.setStudentNo(studentNo);student.setName(name);student.setDingtalkUserId(userId);student.setFirstLoginTime(now);student.setLastLoginTime(now);
            try {students.insert(student);} catch(DuplicateKeyException ex){
                student=students.selectOne(new LambdaQueryWrapper<StudentDO>().eq(StudentDO::getStudentNo,studentNo));
                if(student==null)throw exception(STUDENT_CONFLICT);
            }
        }
        var update=new LambdaUpdateWrapper<StudentDO>().eq(StudentDO::getId,student.getId());
        if(userId!=null)update.and(w->w.isNull(StudentDO::getDingtalkUserId).or().eq(StudentDO::getDingtalkUserId,userId)).set(StudentDO::getDingtalkUserId,userId);
        update.set(StudentDO::getName,name).set(StudentDO::getLastLoginTime,now);
        try {if(students.update(null,update)!=1)throw exception(STUDENT_CONFLICT);}
        catch(DuplicateKeyException ex){throw exception(STUDENT_CONFLICT);}
        return issueToken(student,name);
    }
    private AuthLoginRespVO issueToken(StudentDO student,String name){
        var token=tokens.createAccessToken(student.getId(),UserTypeEnum.MEMBER.getValue(),"cafe-student",null);
        AuthLoginRespVO response=new AuthLoginRespVO();response.setAccessToken(token.getAccessToken());response.setExpiresTime(token.getExpiresTime());response.setStudentNo(student.getStudentNo());response.setName(name);return response;
    }
}
