/**
 * Shared motion preset for every 前端 app (Student / Admin / Barista).
 *
 * Why a preset
 * ------------
 * The Student and Barista `tailwind.config.js` files carried ~130 lines of
 * byte-identical keyframes/animation/easing definitions, while Admin had none at
 * all (so the console could not use the same motion language). Any tweak had to
 * be repeated by hand, which is how the three apps end up feeling like different
 * products.
 *
 * The rule this encodes: one motion vocabulary for the whole system.
 *  - entrances      -> animate-slide-up-content / scale-in / fade-in
 *  - press feedback -> the global button transition in styles/motion.css
 *  - emphasis       -> animate-jelly / cart-bump (use sparingly)
 */

/** Named easings. `luxury`/`silk` are intentionally the same curve. */
export const easings = {
  default: 'cubic-bezier(0.25, 0.8, 0.25, 1)', // 标准：流畅自然
  touch: 'cubic-bezier(0.22, 1, 0.36, 1)',     // 触摸：响应快，回弹柔和
  luxury: 'cubic-bezier(0.16, 1, 0.3, 1)',     // 高级感：起步慢，收尾非常平滑
  silk: 'cubic-bezier(0.16, 1, 0.3, 1)',       // 丝滑感（同 luxury）
  spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)', // 弹簧：有过冲回弹
  linear: 'linear',
};

/**
 * Durations are deliberately longer than the stock Tailwind scale: on a tablet
 * the default 150-200ms transitions read as abrupt.
 */
export const durations = {
  150: '180ms',
  200: '250ms',
  300: '350ms',
  400: '450ms',
  500: '550ms',
  600: '650ms',
  700: '800ms', // 较长的转场
  800: '900ms',
  900: '1000ms',
  1000: '1200ms',
};

const LUXURY = easings.luxury;
const SPRING = easings.spring;

export const keyframes = {
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
    // Sweep the sheen element itself; animating backgroundPosition on a
    // full-size gradient produces no visible movement.
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
};

export const animations = {
  'slide-up-modal': `slideUpModal 0.6s ${LUXURY} backwards`,
  'slide-up-content': `slideUpContent 0.7s ${LUXURY} backwards`,
  'slide-down-content': `slideDownContent 0.7s ${LUXURY} backwards`,
  'scale-in': `scaleIn 0.6s ${LUXURY} backwards`,
  'scale-up': `scaleUp 0.5s ${SPRING} backwards`,
  'fade-in': 'fadeIn 0.5s ease-out backwards',
  'blur-in': `blurIn 1s ${LUXURY} backwards`,
  'text-reveal': `textReveal 0.9s ${LUXURY} backwards`,
  shimmer: 'shimmer 2.5s linear infinite',
  'cart-bump': `cartBump 0.5s ${SPRING}`,
  jelly: 'jelly 0.7s cubic-bezier(0.5, 1.35, 0.4, 1) both',
  float: 'float 4s ease-in-out infinite',
  // Toasts slide in and settle; kept short because they overlay content.
  'toast-in': `slideUpContent 0.35s ${LUXURY} backwards`,
};

export default {
  theme: {
    extend: {
      transitionTimingFunction: easings,
      transitionDuration: durations,
      animation: animations,
      keyframes,
    },
  },
};
