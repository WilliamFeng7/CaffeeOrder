import motion from '../../../packages/shared/tailwind-motion.mjs';

export default {
  // Hover styles only on devices that can hover: taps on iPad/phones no longer leave stuck hover states.
  future: { hoverOnlyWhenSupported: true },
    // The admin console previously had no motion tokens at all, so it could not
    // use the same easing/animation vocabulary as Student and Barista. Wiring the
    // shared preset here makes the three apps move identically.
    presets: [motion],
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
        "../../../packages/shared/src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#103E32',
                secondary: '#DCCA98',
            }
        },
    },
    plugins: [],
}
