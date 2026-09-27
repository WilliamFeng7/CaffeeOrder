/**
 * Motion tokens for code that has to wait for an animation (unmounting after
 * an exit, handing a dragged sheet back to CSS). The values live in
 * styles/motion.css; reading them here keeps timers and CSS from drifting.
 */
const cache = new Map<string, number>();

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
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches ? Math.min(ms, 200) : ms;
}
