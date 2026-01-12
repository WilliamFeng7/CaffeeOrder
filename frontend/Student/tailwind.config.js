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

export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
        "./components/**/*.{vue,js,ts,jsx,tsx}",
        "./*.{vue,js,ts,jsx,tsx}",
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
            // --- 触摸交互优化 (TOUCH ANIMATIONS) ---
            // 自定义过渡曲线 (Transition Timing Functions)
            transitionTimingFunction: {
                'default': 'cubic-bezier(0.25, 0.8, 0.25, 1)', // 标准: 流畅自然
                'touch': 'cubic-bezier(0.22, 1, 0.36, 1)',     // 触摸: 响应快，回弹柔和
                'luxury': 'cubic-bezier(0.16, 1, 0.3, 1)',     // 高级感: 启动慢，结束非常平滑
                'silk': 'cubic-bezier(0.16, 1, 0.3, 1)',       // 丝滑感 (同 Luxury)
                'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)', // 弹簧效果: 有过冲回弹
                'linear': 'linear',
            },
            // 自定义过渡时长 (Transition Durations)
            transitionDuration: {
                '200': '250ms', // 微调时长，稍慢一点以增加质感
                '300': '350ms',
                '400': '450ms',
                '500': '550ms',
                '600': '650ms',
                '700': '800ms', // 用于更长的转场
                '800': '900ms',
                '900': '1000ms',
                '1000': '1200ms',
            },
            // 自定义组合动画 (Animations)
            animation: {
                'slide-up-modal': 'slideUpModal 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards', // 模态窗上滑
                'slide-up-content': 'slideUpContent 0.7s cubic-bezier(0.16, 1, 0.3, 1) both', // 内容上滑渐显
                'slide-down-content': 'slideDownContent 0.7s cubic-bezier(0.16, 1, 0.3, 1) both', // 内容下滑
                'scale-in': 'scaleIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) both',                // 缩放进入
                'scale-up': 'scaleUp 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both',            // 放大强调
                'fade-in': 'fadeIn 0.5s ease-out both',                                       // 淡入
                'blur-in': 'blurIn 1s cubic-bezier(0.16, 1, 0.3, 1) forwards',                // 模糊变清晰
                'text-reveal': 'textReveal 0.9s cubic-bezier(0.16, 1, 0.3, 1) both',          // 文字揭示
                'shimmer': 'shimmer 2.5s linear infinite',                                    // 骨架屏流光
                'cart-bump': 'cartBump 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',               // 购物车跳动
                'jelly': 'jelly 0.7s cubic-bezier(0.5, 1.35, 0.4, 1) both',                   // 果冻Q弹效果 (按钮)
                'float': 'float 4s ease-in-out infinite',                                     // 悬浮漂动
            },
            // 关键帧定义 (Keyframes)
            keyframes: {
                slideUpModal: {
                    '0%': { transform: 'translate3d(0, 100%, 0)' },
                    '100%': { transform: 'translate3d(0, 0, 0)' },
                },
                slideUpContent: {
                    '0%': { transform: 'translate3d(0, 40px, 0)', opacity: '0' },
                    '100%': { transform: 'translate3d(0, 0, 0)', opacity: '1' },
                },
                slideDownContent: {
                    '0%': { transform: 'translate3d(0, -40px, 0)', opacity: '0' },
                    '100%': { transform: 'translate3d(0, 0, 0)', opacity: '1' },
                },
                scaleIn: {
                    '0%': { transform: 'scale(0.9)', opacity: '0' },
                    '100%': { transform: 'scale(1)', opacity: '1' },
                },
                scaleUp: {
                    '0%': { transform: 'scale(0.8)', opacity: '0' },
                    '100%': { transform: 'scale(1)', opacity: '1' },
                },
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                blurIn: {
                    '0%': { opacity: '0', filter: 'blur(20px)', transform: 'scale(1.02)' },
                    '100%': { opacity: '1', filter: 'blur(0)', transform: 'scale(1)' },
                },
                textReveal: {
                    '0%': { clipPath: 'inset(0 0 100% 0)', transform: 'translate3d(0, 20px, 0)' },
                    '100%': { clipPath: 'inset(0 0 0 0)', transform: 'translate3d(0, 0, 0)' },
                },
                shimmer: {
                    '0%': { backgroundPosition: '-200% 0' },
                    '100%': { backgroundPosition: '200% 0' },
                },
                cartBump: {
                    '0%, 100%': { transform: 'scale(1)' },
                    '40%': { transform: 'scale(1.2)' },
                },
                jelly: {
                    '0%': { transform: 'scale(1, 1)' },
                    '30%': { transform: 'scale(1.15, 0.85)' },
                    '40%': { transform: 'scale(0.85, 1.15)' },
                    '50%': { transform: 'scale(1.05, 0.95)' },
                    '65%': { transform: 'scale(0.98, 1.02)' },
                    '75%': { transform: 'scale(1.02, 0.98)' },
                    '100%': { transform: 'scale(1, 1)' },
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-12px)' },
                }
            }
        }
    },
    plugins: [],
}
