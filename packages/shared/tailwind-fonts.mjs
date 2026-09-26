/**
 * Shared font stacks for Student / Admin / Barista.
 *
 * System fonts only: Spline Sans and Playfair came from Google Fonts, which is
 * blocked on mainland networks, so the apps looked different depending on the
 * network and re-flowed when the fonts arrived. On an iPad these resolve to
 * SF Pro + PingFang SC, and to New York for the serif accent.
 */
const sans = [
  '-apple-system', 'BlinkMacSystemFont', '"SF Pro Text"', '"PingFang SC"', '"Hiragino Sans GB"',
  '"Microsoft YaHei"', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif',
];

export default {
  theme: {
    extend: {
      fontFamily: {
        sans,
        display: ['-apple-system', 'BlinkMacSystemFont', '"SF Pro Display"', ...sans.slice(3)],
        serif: ['ui-serif', '"New York"', '"Songti SC"', 'Georgia', 'serif'],
      },
    },
  },
};
