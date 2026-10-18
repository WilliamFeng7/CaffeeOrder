// 时间一律按北京时间显示（docs/architecture.md），和 iPad 的时区设置无关。
const hourMinute = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
    timeZone: 'Asia/Shanghai',
});

/** 毫秒时间戳 → "11:46" */
export const clock = (ms: number) => hourMinute.format(ms);

/** 等了多少分钟；iPad 时钟比服务器慢时不出现负数。 */
export const waitedMinutes = (since: number, now: number) => Math.max(0, Math.floor((now - since) / 60000));

/** 等超过这么多分钟，等待时间改用提醒色。 */
export const LONG_WAIT_MINUTES = 10;

/** "刚下单" / "已等 3 分钟" / "已等 1 小时 5 分" */
export function waited(since: number, now: number): string {
    const minutes = waitedMinutes(since, now);
    if (minutes < 1) return '刚下单';
    if (minutes < 60) return `已等 ${minutes} 分钟`;
    const rest = minutes % 60;
    return `已等 ${Math.floor(minutes / 60)} 小时${rest ? ` ${rest} 分` : ''}`;
}
