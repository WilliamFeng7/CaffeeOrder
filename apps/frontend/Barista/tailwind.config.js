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
import theme from '../../../packages/shared/tailwind-theme.mjs';

export default {
  // Hover styles only on devices that can hover: taps on iPad/phones no longer leave stuck hover states.
  future: { hoverOnlyWhenSupported: true },
    presets: [motion, fonts, theme],
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
        "./components/**/*.{vue,js,ts,jsx,tsx}",
        "./*.{vue,js,ts,jsx,tsx}",
        "../../../packages/shared/src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    // Colors, radii and shadows: packages/shared/tailwind-theme.mjs
    plugins: [],
}
