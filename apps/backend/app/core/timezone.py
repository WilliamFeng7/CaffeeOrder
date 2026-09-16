from datetime import datetime, timedelta, timezone

# --- 时区定义 (Timezone Definitions) ---

# 北京/上海时间 (UTC+8)
CST = timezone(timedelta(hours=8))
# UTC 时间 (Python < 3.11 兼容性)
UTC = timezone.utc


def now_cst() -> datetime:
    """
    获取当前北京时间 (Get Current Beijing Time)

    Returns:
        datetime: 带有时区信息的当前时间对象
    """
    return datetime.now(CST)


def utc_to_cst(dt: datetime) -> datetime:
    """
    将 UTC 时间转换为北京时间 (Convert UTC to CST)
    """
    if dt.tzinfo is None:
        # 如果是 naive datetime (无时区)，默认视为 UTC
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(CST)
