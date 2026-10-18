/** @type {import('tailwindcss').Config} */
// 颜色、圆角和动效沿用共享预设，和学生端保持一致。
import motion from '../../../packages/shared/tailwind-motion.mjs';
import fonts from '../../../packages/shared/tailwind-fonts.mjs';
import theme from '../../../packages/shared/tailwind-theme.mjs';

export default {
    presets: [motion, fonts, theme],
    content: [
        './index.html',
        './src/**/*.{vue,ts}',
        '../../../packages/shared/src/components/AppIcon.vue',
    ],
    theme: {
        extend: {
            colors: {
                // 绿色大卡片（最早的一张待录单）上的次要文字、等太久的提醒和新订单闪烁色。
                'on-primary-sub': 'rgba(255, 255, 255, 0.82)',
                'on-primary-warning': '#F3C77A',
                'primary-flash': '#3C8A6D',
                // 数字键盘按下时的底色、弹层后面的遮罩。
                'cream-pressed': '#E6E4DE',
                scrim: 'rgba(23, 28, 25, 0.38)',
            },
            fontFamily: {
                // 收银单号、时间和数字键盘用圆体数字（iPad 上是 SF Pro Rounded），和杯贴上的号一样好认。
                num: ['ui-rounded', '"SF Pro Rounded"', '-apple-system', 'BlinkMacSystemFont', '"PingFang SC"', 'sans-serif'],
            },
        },
    },
    plugins: [],
};
