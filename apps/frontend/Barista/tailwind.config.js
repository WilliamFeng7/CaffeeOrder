/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
        "./components/**/*.{vue,js,ts,jsx,tsx}",
        "./*.{vue,js,ts,jsx,tsx}",
        "../../../packages/shared/src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: "#103E32",
                "primary-content": "#ffffff",
                secondary: "#DCCA98",
                "secondary-content": "#2C2108",
                "background-light": "#F2F7F5",
                "background-dark": "#0C1F1A",
                "surface-light": "#ffffff",
                "text-main": "#0A2921",
                "text-sub": "#5D736F",
                "wechat": "#07C160",
                "alipay": "#1677FF",
                // KDS-specific colors
                "kds-hot": "#EF4444",
                "kds-iced": "#3B82F6",
                "kds-pending": "#F59E0B",
                "kds-processing": "#6366F1",
                "kds-completed": "#10B981",
                "kds-urgent": "#DC2626",
                "kds-sugar-0": "#E5E7EB",
                "kds-sugar-50": "#FDE68A",
                "kds-sugar-100": "#F59E0B",
                "kds-sugar-120": "#B45309",
            },
            fontFamily: {
                sans: ["Spline Sans", "sans-serif"],
                serif: ["Playfair Display", "serif"],
            },
            transitionTimingFunction: {
                'default': 'cubic-bezier(0.25, 0.8, 0.25, 1)',
                'touch': 'cubic-bezier(0.22, 1, 0.36, 1)',
                'luxury': 'cubic-bezier(0.16, 1, 0.3, 1)',
                'silk': 'cubic-bezier(0.16, 1, 0.3, 1)',
                'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
                'linear': 'linear',
            },
            transitionDuration: {
                '200': '250ms',
                '300': '350ms',
                '400': '450ms',
                '500': '550ms',
                '600': '650ms',
                '700': '800ms',
                '800': '900ms',
                '900': '1000ms',
                '1000': '1200ms',
            },
            animation: {
                'slide-up-modal': 'slideUpModal 0.6s cubic-bezier(0.16, 1, 0.3, 1) backwards',
                'slide-up-content': 'slideUpContent 0.7s cubic-bezier(0.16, 1, 0.3, 1) backwards',
                'slide-down-content': 'slideDownContent 0.7s cubic-bezier(0.16, 1, 0.3, 1) backwards',
                'scale-in': 'scaleIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) backwards',
                'scale-up': 'scaleUp 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) backwards',
                'fade-in': 'fadeIn 0.5s ease-out backwards',
                'blur-in': 'blurIn 1s cubic-bezier(0.16, 1, 0.3, 1) backwards',
                'text-reveal': 'textReveal 0.9s cubic-bezier(0.16, 1, 0.3, 1) backwards',
                'shimmer': 'shimmer 2.5s linear infinite',
                'cart-bump': 'cartBump 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
                'jelly': 'jelly 0.7s cubic-bezier(0.5, 1.35, 0.4, 1) both',
                'float': 'float 4s ease-in-out infinite',
                // KDS-specific animations
                'pulse-urgent': 'pulseUrgent 2s ease-in-out infinite',
                'slide-in-left': 'slideInLeft 0.5s cubic-bezier(0.16, 1, 0.3, 1) both',
                'bounce-in': 'bounceIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both',
                'glow-pulse': 'glowPulse 2s ease-in-out infinite',
            },
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
                    // Sweep the sheen element across its parent (translateX),
                    // backgroundPosition on a full-size gradient is invisible
                    '0%': { transform: 'translateX(-200%) skewX(12deg)' },
                    '100%': { transform: 'translateX(200%) skewX(12deg)' },
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
                },
                // KDS-specific keyframes
                pulseUrgent: {
                    '0%, 100%': { opacity: '1', boxShadow: '0 0 0 0 rgba(220, 38, 38, 0.4)' },
                    '50%': { opacity: '0.85', boxShadow: '0 0 20px 10px rgba(220, 38, 38, 0.2)' },
                },
                slideInLeft: {
                    '0%': { transform: 'translateX(-30px)', opacity: '0' },
                    '100%': { transform: 'translateX(0)', opacity: '1' },
                },
                bounceIn: {
                    '0%': { transform: 'scale(0.3)', opacity: '0' },
                    '50%': { transform: 'scale(1.1)' },
                    '70%': { transform: 'scale(0.9)' },
                    '100%': { transform: 'scale(1)', opacity: '1' },
                },
                glowPulse: {
                    '0%, 100%': { boxShadow: '0 0 5px 0 currentColor' },
                    '50%': { boxShadow: '0 0 20px 5px currentColor' },
                }
            }
        }
    },
    plugins: [],
}
