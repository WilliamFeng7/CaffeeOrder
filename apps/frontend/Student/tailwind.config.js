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
            // 自定义颜色系统 (Custom Color System): 简约 — 暖白底、墨色字、绿色是唯一的强调色
            // Minimal: warm white, near-black ink, one green accent. All text
            // pairs meet 4.5:1 (text-sub also on the `cream` fill).
            colors: {
                primary: "#1B5E47",             // 主色 (森林绿): 主按钮、选中态
                "primary-dark": "#154A38",      // 按下
                "primary-soft": "#EAF1ED",      // 选中态浅底
                "primary-content": "#ffffff",   // 主色上的文本色
                secondary: "#C8963E",           // 焦糖色: 只用于星标这类小图标
                "secondary-soft": "#F7EFE0",    // 点缀浅底
                "secondary-content": "#7A5213", // 点缀浅底上的文字
                "background-light": "#FAFAF7",  // 暖白背景 (Main App BG)
                "background-dark": "#0C1F1A",   // 深色背景
                "surface-light": "#ffffff",     // 白色面板
                cream: "#F2F1EC",               // 图片占位、输入框、分段控件底
                line: "#E9E7E2",                // 细分割线
                "text-main": "#171C19",         // 墨色正文
                "text-sub": "#676C69",          // 次要文本
                "wechat": "#07C160",            // 微信支付色
                "alipay": "#1677FF",            // 支付宝色
            },
            borderRadius: {
                tile: "12px",   // 图片、输入框、小块
                card: "16px",   // 卡片、商品图
                sheet: "24px",  // 底部面板
            },
            // Mostly flat: hairlines and whitespace do the separating; shadows
            // only lift things that float over content.
            boxShadow: {
                card: "0 1px 2px rgba(23, 28, 25, 0.04)",
                float: "0 16px 40px -16px rgba(23, 28, 25, 0.35)",
                sheet: "0 -12px 40px rgba(23, 28, 25, 0.10)",
            },
        }
    },
    plugins: [],
}
