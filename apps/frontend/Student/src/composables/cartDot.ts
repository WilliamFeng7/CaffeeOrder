/**
 * cartDot.ts
 *
 * 加入购物车的小圆点 (The add-to-cart dot): one small dot pops out of the Add
 * button and is tossed into the bag icon of the cart bar like a ball - across
 * at an even pace while it rises and falls - shrinking and fading as it drops
 * in. One element, one transform/opacity animation; nothing else moves.
 */
import { prefersReducedMotion } from '@shared/motion';

const DOT_MS = 560;
const STEPS = 36;

const centre = (r: DOMRect) => ({ x: r.left + r.width / 2, y: r.top + r.height / 2 });
const easeOut = (u: number) => 1 - (1 - u) ** 3;

export function dropDot(from: DOMRect, to: DOMRect): Promise<void> {
  if (prefersReducedMotion()) return Promise.resolve();
  const a = centre(from);
  const b = centre(to);
  // The top of the throw clears the higher end, by more on a longer throw.
  const top = Math.min(a.y, b.y) - Math.min(140, Math.max(72, Math.hypot(b.x - a.x, b.y - a.y) * 0.4));
  // The parabola through both ends that peaks at `top`: y = top + (s·t − ra)².
  const ra = Math.sqrt(a.y - top);
  const s = ra + Math.sqrt(b.y - top);

  const points = Array.from({ length: STEPS + 1 }, (_, i) => {
    const t = i / STEPS;
    return { t, x: a.x + (b.x - a.x) * t, y: top + (s * t - ra) ** 2 };
  });
  // How much of the path is still ahead at each point: the dot shrinks over
  // the last stretch and fades just as it reaches the bag, however fast it
  // is falling by then.
  const ahead = points.map(() => 0);
  for (let i = STEPS - 1; i >= 0; i--) {
    ahead[i] = ahead[i + 1] + Math.hypot(points[i + 1].x - points[i].x, points[i + 1].y - points[i].y);
  }
  const frames: Keyframe[] = points.map(({ t, x, y }, i) => {
    // Pops out of the button over the first few frames.
    const grow = t < 0.15 ? 0.5 + 0.5 * easeOut(t / 0.15) : 1;
    const scale = grow * (0.6 + 0.4 * Math.min(1, ahead[i] / 64));
    return {
      offset: t,
      transform: `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0) scale(${scale.toFixed(3)})`,
      opacity: Number(Math.min(1, ahead[i] / 20).toFixed(3)),
    };
  });

  const dot = document.createElement('span');
  dot.className = 'cart-dot';
  dot.setAttribute('aria-hidden', 'true');
  document.body.appendChild(dot);
  const run = dot.animate(frames, { duration: DOT_MS, easing: 'linear', fill: 'forwards' });
  return run.finished.catch(() => undefined).then(() => { dot.remove(); });
}
