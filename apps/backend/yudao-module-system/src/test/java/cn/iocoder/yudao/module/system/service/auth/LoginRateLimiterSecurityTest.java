package cn.iocoder.yudao.module.system.service.auth;

import cn.hutool.crypto.digest.DigestUtil;
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

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class LoginRateLimiterSecurityTest {
    private final StringRedisTemplate redis = mock(StringRedisTemplate.class);
    private final LoginRateLimiter limiter = new LoginRateLimiter();

    LoginRateLimiterSecurityTest() {
        ReflectionTestUtils.setField(limiter, "redis", redis);
        when(redis.execute(any(RedisScript.class), anyList(), any())).thenReturn(1L);
    }

    @AfterEach void clearRequest() { RequestContextHolder.resetRequestAttributes(); }

    @Test void forwardedHeadersDoNotCreateNewLimiterBuckets() {
        setRequest("10.0.0.8", "198.51.100.4");
        limiter.check("admin");
        setRequest("10.0.0.8", "203.0.113.9");
        limiter.check("admin");

        ArgumentCaptor<List<String>> keys = ArgumentCaptor.forClass((Class) List.class);
        verify(redis, times(4)).execute(any(RedisScript.class), keys.capture(), any());
        List<List<String>> calls = keys.getAllValues();
        String expectedAccount = "system:login:rate:account:" + DigestUtil.sha256Hex("admin");
        String expectedIp = "system:login:rate:ip:" + DigestUtil.sha256Hex("10.0.0.8");
        assertEquals(List.of(expectedAccount), calls.get(0));
        assertEquals(List.of(expectedIp), calls.get(1));
        assertEquals(calls.get(0), calls.get(2));
        assertEquals(calls.get(1), calls.get(3));
    }

    private void setRequest(String remoteAddress, String forwardedFor) {
        MockHttpServletRequest mock = new MockHttpServletRequest();
        mock.setRemoteAddr(remoteAddress);
        mock.addHeader("X-Forwarded-For", forwardedFor);
        RequestContextHolder.setRequestAttributes(new ServletRequestAttributes(mock));
    }
}
