/**
 * Shared motion preset for every 前端 app (Student / Admin / Barista).
 *
 * One motion vocabulary for the whole system. The curves and durations are CSS
 * custom properties defined once in styles/motion.css (so plain CSS, Vue
 * <Transition> classes and inline drag styles all use the same values); this
 * preset only exposes them as Tailwind utilities.
 *
 *  - entrances      -> animate-slide-up-content / scale-in / fade-in
 *  - sheets         -> animate-slide-up-modal, ease-drawer, duration-sheet(-out)
 *  - things that move on screen (indicators, sliders) -> ease-spring duration-spring
 *  - press feedback -> the global button transition in styles/motion.css
 *  - small confirmations (icons, badges) -> animate-icon-pop / .pop-in
 *
 * The feel: long, gliding finishes rather than snaps. Entrances take ~560ms on
 * a strong ease-out (the element is nearly in place early and settles gently),
 * exits run at ~65% of their entrance on an accelerating curve (ease-in), and
 * anything that travels across the screen uses a spring.
 */

/** Named easings (values live in styles/motion.css). */
export const easings = {
  DEFAULT: 'var(--ease-out)',
  out: 'var(--ease-out)',
  in: 'var(--ease-in)',
  'in-out': 'var(--ease-in-out)',
  back: 'var(--ease-back)',
  drawer: 'var(--ease-drawer)',
  spring: 'var(--ease-spring)',
  'spring-soft': 'var(--ease-spring-soft)',
  linear: 'linear',
};

/** Tailwind's numeric scale means what it says; the named steps are the tokens. */
export const durations = {
  DEFAULT: 'var(--dur-color)',
  press: 'var(--dur-press)',
  release: 'var(--dur-release)',
  color: 'var(--dur-color)',
  popover: 'var(--dur-popover)',
  pop: 'var(--dur-pop)',
  'page-out': 'var(--dur-page-out)',
  fade: 'var(--dur-fade)',
  enter: 'var(--dur-enter)',
  sheet: 'var(--dur-sheet-in)',
  'sheet-out': 'var(--dur-sheet-out)',
  spring: 'var(--dur-spring)',
  'spring-soft': 'var(--dur-spring-soft)',
};

export const keyframes = {
  slideUpModal: {
    '0%': { transform: 'translate3d(0, 100%, 0)' },
    '100%': { transform: 'translate3d(0, 0, 0)' },
  },
  slideUpContent: {
    '0%': { transform: 'translate3d(0, 16px, 0)', opacity: '0' },
    '100%': { transform: 'translate3d(0, 0, 0)', opacity: '1' },
  },
  scaleIn: {
    '0%': { transform: 'scale(0.96)', opacity: '0' },
    '100%': { transform: 'scale(1)', opacity: '1' },
  },
  fadeIn: {
    '0%': { opacity: '0' },
    '100%': { opacity: '1' },
  },
  textReveal: {
    '0%': { clipPath: 'inset(0 0 100% 0)', transform: 'translate3d(0, 16px, 0)' },
    '100%': { clipPath: 'inset(0 0 0 0)', transform: 'translate3d(0, 0, 0)' },
  },
  // An icon becoming active: dips a little and springs back past 100%.
  iconPop: {
    '0%': { transform: 'scale(0.82)' },
    '100%': { transform: 'scale(1)' },
  },
};

export const animations = {
  'slide-up-modal': 'slideUpModal var(--dur-sheet-in) var(--ease-drawer) backwards',
  'slide-up-content': 'slideUpContent var(--dur-enter) var(--ease-out) backwards',
  'scale-in': 'scaleIn var(--dur-scale-in) var(--ease-out) backwards',
  'fade-in': 'fadeIn var(--dur-fade) var(--ease-out) backwards',
  'text-reveal': 'textReveal var(--dur-enter) var(--ease-out) backwards',
  'icon-pop': 'iconPop var(--dur-pop) var(--ease-back)',
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
