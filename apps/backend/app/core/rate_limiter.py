import time

from fastapi import HTTPException, Request, status

# --- 简单内存限流器 (Simple In-Memory Rate Limiter) ---
# 存储结构: { 客户端IP: [失败时间戳1, 失败时间戳2, ...] }
# 注意：生产环境建议使用 Redis 以支持多实例部署和持久化。
# Note: Use Redis for production.
_failed_attempts: dict[str, list[float]] = {}

# 配置
LOCKOUT_DURATION = 60  # 锁定时间窗口 (秒) -> 1分钟
MAX_ATTEMPTS = 6  # 窗口内最大请求次数 (允许5次密码尝试，第6次被拦截)

# 清理阈值：窗口外的 key 一律删除，避免字典随流量无限膨胀
_MAX_TRACKED_KEYS = 10000


def _prune_expired(now: float) -> None:
    """Drop keys whose window has fully elapsed so the store stays bounded."""
    if len(_failed_attempts) < _MAX_TRACKED_KEYS:
        return
    for key in [
        k for k, ts in _failed_attempts.items()
        if not ts or now - max(ts) >= LOCKOUT_DURATION
    ]:
        _failed_attempts.pop(key, None)


def _client_key(request: Request) -> str:
    """
    Rate-limit bucket for a request.

    This deliberately keys on the peer IP only. It used to also include a
    client-supplied `device_id` cookie, which let an attacker mint a fresh bucket
    per attempt (just drop/rename the cookie) and bypass the limiter entirely.
    Per-account brute forcing is still covered by the progressive account
    lockout stored on the User row.
    """
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, device_id: str | None = None):
    """
    检查是否超过速率限制 (Check Rate Limit)

    采用滑动窗口算法 (Sliding Window Algorithm):
    只计算最近 LOCKOUT_DURATION 秒内的失败次数。

    `device_id` 参数保留仅为兼容既有调用方，已不再参与限流键计算。
    """
    key = _client_key(request)
    now = time.time()

    # 1. 清理过期记录 (Clean up old attempts)
    if key in _failed_attempts:
        # 只保留窗口期内的时间戳
        _failed_attempts[key] = [
            t for t in _failed_attempts[key] if now - t < LOCKOUT_DURATION
        ]

    current_attempts = len(_failed_attempts.get(key, []))

    # 2. 判断是否超限 (Check Threshold)
    if current_attempts >= MAX_ATTEMPTS:
        # 计算剩余等待时间 (Calculate Retry-After)
        oldest_fail = min(_failed_attempts[key])
        retry_after = int(LOCKOUT_DURATION - (now - oldest_fail))

        # 抛出 429 错误
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试过于频繁，请等待 {retry_after} 秒后重试 (Too many attempts)",
        )

    return MAX_ATTEMPTS - current_attempts


def record_failed_attempt(request: Request, device_id: str | None = None) -> None:
    """
    记录一次失败尝试 (Record Failed Attempt)
    """
    key = _client_key(request)
    now = time.time()

    _failed_attempts.setdefault(key, []).append(now)
    _prune_expired(now)
