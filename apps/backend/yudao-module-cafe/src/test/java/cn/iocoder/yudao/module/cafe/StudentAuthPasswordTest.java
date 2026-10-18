package cn.iocoder.yudao.module.cafe;

import cn.iocoder.yudao.framework.common.exception.ServiceException;
import cn.iocoder.yudao.framework.common.enums.UserTypeEnum;
import cn.iocoder.yudao.module.cafe.controller.app.auth.vo.AuthLoginRespVO;
import cn.iocoder.yudao.module.cafe.dal.dataobject.StudentDO;
import cn.iocoder.yudao.module.cafe.dal.mysql.StudentMapper;
import cn.iocoder.yudao.module.cafe.service.auth.StudentAuthServiceImpl;
import cn.iocoder.yudao.module.cafe.service.auth.StudentLoginRateLimiter;
import cn.iocoder.yudao.module.system.dal.dataobject.oauth2.OAuth2AccessTokenDO;
import cn.iocoder.yudao.module.system.service.oauth2.OAuth2TokenService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;

import static cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.STUDENT_CREDENTIALS_INVALID;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class StudentAuthPasswordTest {

    @Mock private StudentMapper students;
    @Mock private PasswordEncoder passwordEncoder;
    @Mock private OAuth2TokenService tokens;
    @Mock private StudentLoginRateLimiter rateLimiter;
    @InjectMocks private StudentAuthServiceImpl service;

    @BeforeEach
    void setClock() {
        ReflectionTestUtils.setField(service, "cafeClock", Clock.fixed(
                Instant.parse("2026-10-17T04:00:00Z"), ZoneId.of("Asia/Shanghai")));
    }

    @Test
    void correctPasswordIssuesStudentTokenWithoutChangingIdentity() {
        StudentDO student = new StudentDO().setId(7L).setStudentNo("S2026001")
                .setName("测试学生").setPasswordHash("stored-hash");
        when(students.selectOne(any())).thenReturn(student);
        when(passwordEncoder.matches("correct-password", "stored-hash")).thenReturn(true);
        when(students.updateById(student)).thenReturn(1);
        OAuth2AccessTokenDO token = new OAuth2AccessTokenDO();
        token.setAccessToken("access-token");
        token.setExpiresTime(LocalDateTime.of(2026, 10, 24, 12, 0));
        when(tokens.createAccessToken(7L, UserTypeEnum.MEMBER.getValue(), "cafe-student", null))
                .thenReturn(token);

        AuthLoginRespVO result = service.passwordLogin("S2026001", "correct-password");

        assertEquals("access-token", result.getAccessToken());
        assertEquals("S2026001", result.getStudentNo());
        assertEquals("测试学生", result.getName());
        verify(rateLimiter).reset("S2026001");
    }

    @Test
    void wrongPasswordAndUnknownStudentUseTheSamePublicError() {
        StudentDO student = new StudentDO().setId(7L).setStudentNo("S2026001")
                .setName("测试学生").setPasswordHash("stored-hash");
        when(students.selectOne(any())).thenReturn(student, (StudentDO) null);
        when(passwordEncoder.matches(anyString(), anyString())).thenReturn(false);

        ServiceException wrongPassword = assertThrows(ServiceException.class,
                () -> service.passwordLogin("S2026001", "wrong-password"));
        ServiceException unknownStudent = assertThrows(ServiceException.class,
                () -> service.passwordLogin("S9999999", "wrong-password"));

        assertEquals(STUDENT_CREDENTIALS_INVALID.getCode(), wrongPassword.getCode());
        assertEquals(STUDENT_CREDENTIALS_INVALID.getCode(), unknownStudent.getCode());
        verify(tokens, never()).createAccessToken(any(), any(), anyString(), any());
    }
}
