/**
 * Motion tokens for code that has to wait for an animation (unmounting after
 * an exit, handing a dragged sheet back to CSS) or has to animate something CSS
 * cannot (a number counting). The values live in styles/motion.css; reading
 * them here keeps timers and CSS from drifting.
 */
const cache = new Map<string, number>();

export const prefersReducedMotion = (): boolean =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/** A `--dur-*` token in milliseconds (200ms at most under reduced motion). */
export function motionMs(token: string, fallback: number): number {
  if (typeof window === 'undefined') return fallback;
  let ms = cache.get(token);
  if (ms === undefined) {
    const raw = getComputedStyle(document.documentElement).getPropertyValue(token).trim();
    const value = raw.endsWith('ms') ? parseFloat(raw) : raw.endsWith('s') ? parseFloat(raw) * 1000 : NaN;
    ms = Number.isFinite(value) ? value : fallback;
    cache.set(token, ms);
  }
  // Reduced motion keeps only 200ms colour/opacity fades (see motion.css).
  return prefersReducedMotion() ? Math.min(ms, 200) : ms;
}

/**
 * CSS `cubic-bezier()` as a function of progress, for JS-driven motion that
 * must use the same curves as the stylesheet.
 */
export function cubicBezier(x1: number, y1: number, x2: number, y2: number): (t: number) => number {
  const cx = 3 * x1;
  const bx = 3 * (x2 - x1) - cx;
  const ax = 1 - cx - bx;
  const cy = 3 * y1;
  const by = 3 * (y2 - y1) - cy;
  const ay = 1 - cy - by;
  const x = (t: number) => ((ax * t + bx) * t + cx) * t;
  const y = (t: number) => ((ay * t + by) * t + cy) * t;
  const dx = (t: number) => (3 * ax * t + 2 * bx) * t + cx;

  // Solve x(t) = p: Newton first, bisection if the slope is too flat.
  const solve = (p: number) => {
    let t = p;
    for (let i = 0; i < 8; i++) {
      const err = x(t) - p;
      if (Math.abs(err) < 1e-6) return t;
      const d = dx(t);
      if (Math.abs(d) < 1e-6) break;
      t -= err / d;
    }
    let lo = 0;
    let hi = 1;
    t = p;
    for (let i = 0; i < 30; i++) {
      const v = x(t);
      if (Math.abs(v - p) < 1e-6) break;
      if (v < p) lo = t;
      else hi = t;
      t = (lo + hi) / 2;
    }
    return t;
  };

  return (p: number) => (p <= 0 ? 0 : p >= 1 ? 1 : y(solve(p)));
}

/** --ease-out, cubic-bezier(0.23, 1, 0.32, 1). */
export const easeOut = cubicBezier(0.23, 1, 0.32, 1);
