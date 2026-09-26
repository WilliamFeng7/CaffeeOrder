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

export default {
  // Hover styles only on devices that can hover: taps on iPad/phones no longer leave stuck hover states.
  future: { hoverOnlyWhenSupported: true },
    // Motion tokens (easing/duration/keyframes/animations) come from the shared
    // preset so Student / Admin / Barista cannot drift apart.
    presets: [motion],
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
            // 自定义颜色系统 (Custom Color System)
            colors: {
                primary: "#103E32",             // 主色调 (深绿)
                "primary-content": "#ffffff",   // 主色上的文本色
                secondary: "#DCCA98",           // 辅助色 (金色)
                "secondary-content": "#2C2108", // 辅助色上的文本色
                "background-light": "#F2F7F5",  // 浅色背景 (Main App BG)
                "background-dark": "#0C1F1A",   // 深色背景
                "surface-light": "#ffffff",     // 卡片/模块背景
                "text-main": "#0A2921",         // 主要文本色
                "text-sub": "#5D736F",          // 次要文本色
                "wechat": "#07C160",            // 微信支付色
                "alipay": "#1677FF",            // 支付宝色
            },
            // 自定义字体栈
            fontFamily: {
                sans: ["Spline Sans", "sans-serif"],    // 无衬线体 (UI 主要字体)
                serif: ["Playfair Display", "serif"],   // 衬线体 (标题/强调)
            },
        }
    },
    plugins: [],
}
