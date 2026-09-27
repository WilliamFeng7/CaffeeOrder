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
import theme from '../../../packages/shared/tailwind-theme.mjs';

export default {
  // Hover styles only on devices that can hover: taps on iPad/phones no longer leave stuck hover states.
  future: { hoverOnlyWhenSupported: true },
    // Motion tokens (easing/duration/keyframes/animations) come from the shared
    // preset so Student / Admin / Barista cannot drift apart.
    presets: [motion, fonts, theme],
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
        "./components/**/*.{vue,js,ts,jsx,tsx}",
        "./*.{vue,js,ts,jsx,tsx}",
        "../../../packages/shared/src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    darkMode: 'class', // 支持暗黑模式 (通过 class 切换)
    // Colors, radii and shadows: packages/shared/tailwind-theme.mjs
    plugins: [],
}
