package cn.iocoder.yudao.module.cafe.service.auth;

import cn.iocoder.yudao.framework.common.util.validation.PasswordPolicyUtils;
import cn.iocoder.yudao.module.cafe.dal.dataobject.StudentDO;
import cn.iocoder.yudao.module.cafe.dal.mysql.StudentMapper;
import cn.iocoder.yudao.module.cafe.framework.CafeProperties;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.time.Clock;
import java.time.LocalDateTime;

/**
 * 为显式配置的测试学生设置一次性密码。已有密码绝不因重启被覆盖；
 * 未配置环境变量时不会创建任何账号。
 */
@Slf4j
@Component
public class StudentPasswordBootstrap implements ApplicationRunner {

    @Resource
    private CafeProperties properties;
    @Resource
    private StudentMapper students;
    @Resource
    private PasswordEncoder passwordEncoder;
    @Resource
    private Clock cafeClock;

    @Override
    public void run(ApplicationArguments args) {
        var auth = properties.getAuth();
        if (!auth.isPasswordLoginEnabled()) {
            return;
        }
        String studentNo = trim(auth.getBootstrapStudentNo());
        String password = auth.getBootstrapStudentPassword();
        if (studentNo.isEmpty() && (password == null || password.isEmpty())) {
            return;
        }
        if (!studentNo.matches("[A-Za-z0-9_-]{1,40}")) {
            throw new IllegalStateException("cafe.auth.bootstrap-student-no 格式不正确");
        }
        if (!PasswordPolicyUtils.isValid(password)) {
            throw new IllegalStateException("cafe.auth.bootstrap-student-password 必须满足："
                    + PasswordPolicyUtils.MESSAGE);
        }

        StudentDO student = students.selectOne(new LambdaQueryWrapper<StudentDO>()
                .eq(StudentDO::getStudentNo, studentNo));
        if (student != null && student.getPasswordHash() != null && !student.getPasswordHash().isBlank()) {
            log.info("测试学生 {} 已有密码，跳过初始化", studentNo);
            return;
        }

        String hash = passwordEncoder.encode(password);
        if (student == null) {
            LocalDateTime now = LocalDateTime.now(cafeClock);
            student = new StudentDO()
                    .setStudentNo(studentNo)
                    .setName(trim(auth.getBootstrapStudentName()))
                    .setPasswordHash(hash)
                    .setFirstLoginTime(now)
                    .setLastLoginTime(now);
            try {
                students.insert(student);
                log.info("已创建测试学生账号 {}", studentNo);
            } catch (DuplicateKeyException ignored) {
                student = students.selectOne(new LambdaQueryWrapper<StudentDO>()
                        .eq(StudentDO::getStudentNo, studentNo));
                if (student == null) {
                    throw new IllegalStateException("测试学生账号初始化发生并发冲突");
                }
            }
            return;
        }

        student.setPasswordHash(hash);
        students.updateById(student);
        log.info("已为测试学生 {} 设置初始密码", studentNo);
    }

    private static String trim(String value) {
        return value == null ? "" : value.trim();
    }
}
