/**
 * spring.ts
 *
 * 弹簧动画 (A tiny spring animator) for gesture-driven motion. Unlike a CSS
 * transition it starts from wherever the element is, takes the finger's
 * release velocity, and can be stopped or retargeted mid-flight - so a swipe
 * hands off into the animation without a seam.
 *
 * Apple-style parameters: `response` (seconds, how quickly it gets there -
 * not a duration) and `dampingRatio` (1 = settles with no overshoot, 0.8 = a
 * little bounce, for moves that were flicked).
 */
export interface SpringOptions {
  response?: number;
  dampingRatio?: number;
  /** Starting velocity in units per second (e.g. the finger's px/s). */
  velocity?: number;
  onUpdate: (value: number) => void;
  onComplete?: () => void;
}

export interface SpringHandle {
  stop(): void;
}

const reducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export function spring(from: number, to: number, opts: SpringOptions): SpringHandle {
  const { response = 0.45, dampingRatio = 1, onUpdate, onComplete } = opts;
  let x = from;
  let v = opts.velocity ?? 0;

  if (reducedMotion() || (from === to && v === 0)) {
    onUpdate(to);
    onComplete?.();
    return { stop() {} };
  }

  // Unit mass: stiffness from the response, damping from the ratio.
  const k = (2 * Math.PI / response) ** 2;
  const c = (4 * Math.PI * dampingRatio) / response;
  let frame = 0;
  let last = -1;
  let stopped = false;

  const step = (now: number) => {
    if (stopped) return;
    if (last < 0) last = now;
    const dt = Math.min(0.064, (now - last) / 1000);
    last = now;
    // Semi-implicit Euler in 4ms sub-steps keeps stiff springs stable.
    const n = Math.max(1, Math.ceil(dt / 0.004));
    const h = dt / n;
    for (let i = 0; i < n; i++) {
      v += (-k * (x - to) - c * v) * h;
      x += v * h;
    }
    if (Math.abs(x - to) < 0.3 && Math.abs(v) < 2) {
      onUpdate(to);
      onComplete?.();
      return;
    }
    onUpdate(x);
    frame = requestAnimationFrame(step);
  };

  frame = requestAnimationFrame(step);
  return {
    stop() {
      stopped = true;
      cancelAnimationFrame(frame);
    },
  };
}

/** Where a flick would come to rest (Apple's projection; 0.99 = a pager's quick deceleration). */
export const project = (velocityPerSecond: number, decelerationRate = 0.99) =>
  ((velocityPerSecond / 1000) * decelerationRate) / (1 - decelerationRate);

/** iOS rubber band: the further past an edge, the less it follows the finger. */
export const rubberband = (overshoot: number, dimension: number, constant = 0.55) =>
  (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot));

/**
 * Pointer velocity from the last ~100ms of samples, in px per second.
 * Keep pushing { t, v } while dragging; read it on release.
 */
export class VelocityTracker {
  private samples: { t: number; v: number }[] = [];

  push(value: number, t = performance.now()) {
    this.samples.push({ t, v: value });
    while (this.samples.length > 2 && t - this.samples[0].t > 100) this.samples.shift();
  }

  reset() {
    this.samples = [];
  }

  get velocity(): number {
    if (this.samples.length < 2) return 0;
    const a = this.samples[0];
    const b = this.samples[this.samples.length - 1];
    const dt = b.t - a.t;
    return dt > 0 ? ((b.v - a.v) / dt) * 1000 : 0;
  }
}
