/** @type {import('tailwindcss').Config} */
/**
 * tailwind.config.js
 * 
 * Tailwind CSS 配置文件.
 * 
 * 主要功能 (Core Features):
 * 1. 内容扫描 (Content Source): 指定需要扫描的 Vue/JS/TS 文件。
 * 2. 主题扩展 (Theme Extension):
 *    - 调色板 (Colors): 定义品牌色 (Primary/Secondary) 和语义化颜色。
 *    - 字体 (Fonts): 定义主要字体和衬线字体。
 *    - 动画 (Animations): 定义触摸优化的过渡曲线 (bezier) 和复杂关键帧动画 (slide-up, jelly 等)。
 */

import motion from '../../../packages/shared/tailwind-motion.mjs';
import fonts from '../../../packages/shared/tailwind-fonts.mjs';

export default {
  // Hover styles only on devices that can hover: taps on iPad/phones no longer leave stuck hover states.
  future: { hoverOnlyWhenSupported: true },
    // Motion tokens (easing/duration/keyframes/animations) come from the shared
    // preset so Student / Admin / Barista cannot drift apart.
    presets: [motion, fonts],
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
        "./components/**/*.{vue,js,ts,jsx,tsx}",
        "./*.{vue,js,ts,jsx,tsx}",
        "../../../packages/shared/src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    darkMode: 'class', // 支持暗黑模式 (通过 class 切换)
    theme: {
        extend: {
            // 自定义颜色系统 (Custom Color System): 咖啡馆的绿 + 奶油色底
            // All text pairs meet 4.5:1 (text-sub on the cream background too).
            colors: {
                primary: "#1B5E47",             // 主色调 (森林绿): 按钮、选中态
                "primary-dark": "#144835",      // 按下
                "primary-soft": "#E7F0EA",      // 选中态浅底
                "primary-content": "#ffffff",   // 主色上的文本色
                secondary: "#C8963E",           // 焦糖色: 星标、推荐等点缀 (只用于图标/大字)
                "secondary-soft": "#FAF1E1",    // 点缀浅底
                "secondary-content": "#7A5213", // 点缀浅底上的文字
                "background-light": "#F6F4EE",  // 奶油色背景 (Main App BG)
                "background-dark": "#0C1F1A",   // 深色背景
                "surface-light": "#ffffff",     // 卡片/模块背景
                cream: "#EFEAE0",               // 图片占位、分段控件底
                line: "#E7E1D6",                // 分割线、描边
                "text-main": "#1B2A23",         // 主要文本色
                "text-sub": "#5F6E66",          // 次要文本色
                "wechat": "#07C160",            // 微信支付色
                "alipay": "#1677FF",            // 支付宝色
            },
            borderRadius: {
                tile: "14px",   // 图片、输入框、小块
                card: "20px",   // 卡片
                sheet: "28px",  // 底部面板
            },
            // Small blur radii: cheap to paint while scrolling on an iPad.
            boxShadow: {
                card: "0 1px 2px rgba(27, 42, 35, 0.04), 0 6px 16px -8px rgba(27, 42, 35, 0.12)",
                float: "0 12px 28px -12px rgba(27, 42, 35, 0.35)",
                sheet: "0 -8px 32px rgba(27, 42, 35, 0.12)",
            },
        }
    },
    plugins: [],
}
