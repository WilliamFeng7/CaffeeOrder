package cn.iocoder.yudao.module.cafe.service.auth;

import cn.hutool.crypto.digest.DigestUtil;
import cn.iocoder.yudao.framework.common.util.servlet.ServletUtils;
import jakarta.annotation.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Locale;

import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.cafe.enums.ErrorCodeConstants.STUDENT_LOGIN_RATE_LIMITED;

/** 学生账号密码登录的账号与来源 IP 双维度固定窗口限流。 */
@Component
public class StudentLoginRateLimiter {

    private static final int ACCOUNT_LIMIT = 5;
    private static final int IP_LIMIT = 30;
    private static final long WINDOW_SECONDS = 60;
    private static final String ACCOUNT_PREFIX = "cafe:student-login:account:";
    private static final String IP_PREFIX = "cafe:student-login:ip:";
    private static final DefaultRedisScript<Long> INCREMENT = new DefaultRedisScript<>(
            "local count = redis.call('INCR', KEYS[1]); " +
                    "if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]); end; return count;",
            Long.class);

    @Resource
    private StringRedisTemplate redis;

    public void check(String studentNo) {
        String ip = clientAddress();
        if (increment(accountKey(studentNo)) > ACCOUNT_LIMIT
                || increment(IP_PREFIX + DigestUtil.sha256Hex(ip)) > IP_LIMIT) {
            throw exception(STUDENT_LOGIN_RATE_LIMITED);
        }
    }

    public void reset(String studentNo) {
        redis.delete(accountKey(studentNo));
    }

    /** 使用直连地址，避免调用方伪造转发头绕过限流。 */
    private String clientAddress() {
        var request = ServletUtils.getRequest();
        if (request == null || request.getRemoteAddr() == null || request.getRemoteAddr().isBlank()) {
            return "unknown";
        }
        return request.getRemoteAddr();
    }

    private String accountKey(String studentNo) {
        String normalized = studentNo == null ? "" : studentNo.trim().toUpperCase(Locale.ROOT);
        return ACCOUNT_PREFIX + DigestUtil.sha256Hex(normalized);
    }

    private long increment(String key) {
        Long count = redis.execute(INCREMENT, List.of(key), String.valueOf(WINDOW_SECONDS));
        return count == null ? 0 : count;
    }
}
