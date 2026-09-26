/** @type {import('tailwindcss').Config} */
/**
 * Barista (KDS) Tailwind config.
 *
 * The ~115 lines of keyframes/animations/easing previously duplicated here
 * (copied from the Student app) now come from the shared motion preset, so all
 * three products move the same way. Only the KDS palette and its one bespoke
 * effect remain.
 */
import motion from '../../../packages/shared/tailwind-motion.mjs';
import fonts from '../../../packages/shared/tailwind-fonts.mjs';

export default {
  // Hover styles only on devices that can hover: taps on iPad/phones no longer leave stuck hover states.
  future: { hoverOnlyWhenSupported: true },
    presets: [motion, fonts],
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
            // KDS-only effect, not part of the shared motion vocabulary.
            // Tailwind merges these with the preset's keyframes/animations.
            keyframes: {
                glowPulse: {
                    '0%, 100%': { boxShadow: '0 0 5px 0 currentColor' },
                    '50%': { boxShadow: '0 0 20px 5px currentColor' },
                }
            },
            animation: {
                'glow-pulse': 'glowPulse 2s ease-in-out infinite',
            },
        }
    },
    plugins: [],
}
