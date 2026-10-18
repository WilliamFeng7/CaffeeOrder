package cn.iocoder.yudao.module.system.service.auth;

import cn.hutool.crypto.digest.DigestUtil;
import cn.iocoder.yudao.framework.common.util.servlet.ServletUtils;
import jakarta.annotation.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;
import java.util.List;
import java.util.Locale;
import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.system.enums.ErrorCodeConstants.AUTH_LOGIN_RATE_LIMITED;

/** 管理端登录的账号与 IP 双维度固定窗口限流；计数和过期时间在 Redis 中原子完成。 */
@Component
public class LoginRateLimiter {
    private static final int ACCOUNT_LIMIT = 5;
    private static final int IP_LIMIT = 30;
    private static final long WINDOW_SECONDS = 60;
    private static final String ACCOUNT_PREFIX = "system:login:rate:account:";
    private static final String IP_PREFIX = "system:login:rate:ip:";
    private static final DefaultRedisScript<Long> INCREMENT = new DefaultRedisScript<>(
            "local count = redis.call('INCR', KEYS[1]); " +
            "if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]); end; return count;", Long.class);

    @Resource private StringRedisTemplate redis;

    public void check(String username) {
        String ip = clientAddress();
        String accountKey = accountKey(username);
        String ipKey = IP_PREFIX + DigestUtil.sha256Hex(ip);
        if (increment(accountKey) > ACCOUNT_LIMIT || increment(ipKey) > IP_LIMIT) {
            throw exception(AUTH_LOGIN_RATE_LIMITED);
        }
    }

    public void reset(String username) {
        redis.delete(accountKey(username));
    }

    /** Use the socket peer by default; forwarding headers are caller-controlled. */
    private String clientAddress() {
        var request = ServletUtils.getRequest();
        if (request == null) return "unknown";
        String address = request.getRemoteAddr();
        return address == null || address.isBlank() ? "unknown" : address;
    }

    private String accountKey(String username) {
        String normalized = username == null ? "" : username.trim().toLowerCase(Locale.ROOT);
        return ACCOUNT_PREFIX + DigestUtil.sha256Hex(normalized);
    }

    private long increment(String key) {
        Long count = redis.execute(INCREMENT, List.of(key), String.valueOf(WINDOW_SECONDS));
        return count == null ? 0 : count;
    }
}
