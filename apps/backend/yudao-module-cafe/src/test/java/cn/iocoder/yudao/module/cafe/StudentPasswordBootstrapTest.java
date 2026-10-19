package cn.iocoder.yudao.module.cafe;

import cn.iocoder.yudao.module.cafe.dal.dataobject.StudentDO;
import cn.iocoder.yudao.module.cafe.dal.mysql.StudentMapper;
import cn.iocoder.yudao.module.cafe.framework.CafeProperties;
import cn.iocoder.yudao.module.cafe.service.auth.StudentPasswordBootstrap;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class StudentPasswordBootstrapTest {

    @Mock private StudentMapper students;
    @Mock private PasswordEncoder passwordEncoder;
    @InjectMocks private StudentPasswordBootstrap bootstrap;

    @BeforeEach
    void setClock() {
        org.springframework.test.util.ReflectionTestUtils.setField(bootstrap, "cafeClock",
                Clock.fixed(Instant.parse("2026-10-17T04:00:00Z"), ZoneId.of("Asia/Shanghai")));
    }

    @Test
    void explicitBootstrapCreatesHashedStudentPassword() {
        CafeProperties properties = properties("S2026001", "strong-test-pass1");
        when(passwordEncoder.encode("strong-test-pass1")).thenReturn("bcrypt-hash");

        org.springframework.test.util.ReflectionTestUtils.setField(bootstrap, "properties", properties);
        when(students.insert(any(StudentDO.class))).thenReturn(1);
        bootstrap.run(null);

        ArgumentCaptor<StudentDO> captured = ArgumentCaptor.forClass(StudentDO.class);
        verify(students).insert(captured.capture());
        assertEquals("S2026001", captured.getValue().getStudentNo());
        assertEquals("测试学生", captured.getValue().getName());
        assertEquals("bcrypt-hash", captured.getValue().getPasswordHash());
        assertNotEquals("strong-test-pass1", captured.getValue().getPasswordHash());
    }

    @Test
    void existingPasswordIsNotResetOnRestart() {
        CafeProperties properties = properties("S2026001", "strong-test-pass1");
        org.springframework.test.util.ReflectionTestUtils.setField(bootstrap, "properties", properties);
        when(students.selectOne(any())).thenReturn(
                new StudentDO().setId(1L).setPasswordHash("existing-hash"));

        bootstrap.run(null);

        verify(passwordEncoder, never()).encode(any());
        verify(students, never()).updateById(any(StudentDO.class));
    }

    @Test
    void shortBootstrapPasswordFailsClosed() {
        CafeProperties properties = properties("S2026001", "short");
        org.springframework.test.util.ReflectionTestUtils.setField(bootstrap, "properties", properties);

        assertThrows(IllegalStateException.class, () -> bootstrap.run(null));
        verify(students, never()).insert(any(StudentDO.class));
    }

    @Test
    void simpleLetterAndDigitBootstrapPasswordIsAccepted() {
        CafeProperties properties = properties("student", "student123");
        when(passwordEncoder.encode("student123")).thenReturn("dev-hash");
        when(students.insert(any(StudentDO.class))).thenReturn(1);
        org.springframework.test.util.ReflectionTestUtils.setField(bootstrap, "properties", properties);

        bootstrap.run(null);

        ArgumentCaptor<StudentDO> captured = ArgumentCaptor.forClass(StudentDO.class);
        verify(students).insert(captured.capture());
        assertEquals("student", captured.getValue().getStudentNo());
        assertEquals("dev-hash", captured.getValue().getPasswordHash());
    }

    private static CafeProperties properties(String studentNo, String password) {
        CafeProperties properties = new CafeProperties();
        properties.getAuth().setPasswordLoginEnabled(true);
        properties.getAuth().setBootstrapStudentNo(studentNo);
        properties.getAuth().setBootstrapStudentPassword(password);
        return properties;
    }
}
