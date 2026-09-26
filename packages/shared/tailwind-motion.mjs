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
  default: 'cubic-bezier(0.23, 1, 0.32, 1)', // 标准：流畅自然
  touch: 'cubic-bezier(0.22, 1, 0.36, 1)',     // 触摸：响应快，回弹柔和
  luxury: 'cubic-bezier(0.16, 1, 0.3, 1)',     // 高级感：起步慢，收尾非常平滑
  silk: 'cubic-bezier(0.16, 1, 0.3, 1)',       // 丝滑感（同 luxury）
  spring: 'cubic-bezier(0.34, 1.25, 0.64, 1)', // 弹簧：有过冲回弹
  linear: 'linear',
};

/**
 * UI motion stays at or under ~300ms: the old scale stretched duration-700 to
 * 800ms and duration-1000 to 1.2s, which made every tap feel sluggish.
 */
export const durations = {
  150: '150ms',
  200: '200ms',
  300: '250ms',
  400: '280ms',
  500: '300ms',
  600: '300ms',
  700: '300ms',
  800: '350ms',
  900: '400ms',
  1000: '450ms',
};

const LUXURY = easings.luxury;
const SPRING = easings.spring;

export const keyframes = {
  slideUpModal: {
    '0%': { transform: 'translate3d(0, 100%, 0)' },
    '100%': { transform: 'translate3d(0, 0, 0)' },
  },
  slideUpContent: {
    '0%': { transform: 'translate3d(0, 12px, 0)', opacity: '0' },
    '100%': { transform: 'translate3d(0, 0, 0)', opacity: '1' },
  },
  slideDownContent: {
    '0%': { transform: 'translate3d(0, -12px, 0)', opacity: '0' },
    '100%': { transform: 'translate3d(0, 0, 0)', opacity: '1' },
  },
  scaleIn: {
    '0%': { transform: 'scale(0.95)', opacity: '0' },
    '100%': { transform: 'scale(1)', opacity: '1' },
  },
  scaleUp: {
    '0%': { transform: 'scale(0.95)', opacity: '0' },
    '100%': { transform: 'scale(1)', opacity: '1' },
  },
  fadeIn: {
    '0%': { opacity: '0' },
    '100%': { opacity: '1' },
  },
  blurIn: {
    // No filter: animating blur repaints the whole element every frame.
    '0%': { opacity: '0', transform: 'scale(1.02)' },
    '100%': { opacity: '1', transform: 'scale(1)' },
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
    '50%': { transform: 'translateY(-4px)' },
  },
};

export const animations = {
  'slide-up-modal': `slideUpModal 0.36s cubic-bezier(0.32, 0.72, 0, 1) backwards`,
  'slide-up-content': `slideUpContent 0.3s ${LUXURY} backwards`,
  'slide-down-content': `slideDownContent 0.3s ${LUXURY} backwards`,
  'scale-in': `scaleIn 0.25s ${LUXURY} backwards`,
  'scale-up': `scaleUp 0.25s ${LUXURY} backwards`,
  'fade-in': 'fadeIn 0.2s ease-out backwards',
  'blur-in': `blurIn 0.35s ${LUXURY} backwards`,
  'text-reveal': `textReveal 0.4s ${LUXURY} backwards`,
  // Loops are for loading states only: the shimmer runs on skeletons.
  shimmer: 'shimmer 1.5s linear infinite',
  'cart-bump': `cartBump 0.3s ${SPRING}`,
  jelly: 'cartBump 0.3s cubic-bezier(0.34, 1.25, 0.64, 1) both',
  // Decorative floating was an endless loop; it now settles once.
  float: 'fadeIn 0.3s ease-out backwards',
  'toast-in': `slideUpContent 0.3s ${LUXURY} backwards`,
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
