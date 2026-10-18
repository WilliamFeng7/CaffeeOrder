package cn.iocoder.yudao.module.cafe;

import cn.hutool.crypto.digest.DigestUtil;
import cn.iocoder.yudao.module.cafe.service.auth.StudentLoginRateLimiter;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.RedisScript;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class StudentLoginRateLimiterTest {

    private final StringRedisTemplate redis = mock(StringRedisTemplate.class);
    private final StudentLoginRateLimiter limiter = new StudentLoginRateLimiter();

    StudentLoginRateLimiterTest() {
        ReflectionTestUtils.setField(limiter, "redis", redis);
        when(redis.execute(any(RedisScript.class), anyList(), any())).thenReturn(1L);
    }

    @AfterEach
    void clearRequest() {
        RequestContextHolder.resetRequestAttributes();
    }

    @Test
    void accountBucketDoesNotResetWhenTheAttackerChangesIp() {
        setRequest("10.0.0.8");
        limiter.check("s2026001");
        setRequest("10.0.0.9");
        limiter.check("S2026001");

        ArgumentCaptor<List<String>> keys = ArgumentCaptor.forClass((Class) List.class);
        verify(redis, times(4)).execute(any(RedisScript.class), keys.capture(), any());
        List<List<String>> calls = keys.getAllValues();
        String account = "cafe:student-login:account:" + DigestUtil.sha256Hex("S2026001");
        assertEquals(List.of(account), calls.get(0));
        assertEquals(calls.get(0), calls.get(2));
    }

    private void setRequest(String remoteAddress) {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setRemoteAddr(remoteAddress);
        RequestContextHolder.setRequestAttributes(new ServletRequestAttributes(request));
    }
}
