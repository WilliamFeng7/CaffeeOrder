/**
 * genie.ts
 *
 * 像 Mac 最小化那样缩进去 (Minimise like macOS: the "genie").
 *
 * The element is shown as thin horizontal strips, each a copy of it clipped to
 * one band, and every strip is mapped onto a four-cornered shape with a
 * projective transform (matrix3d), so the copy can bend into a funnel without
 * tearing: the bands nearest the target set off first and the rest follow,
 * each narrowing towards the target faster than it travels, until the whole
 * element has poured into the target point. Strips share their edges, so the
 * picture stays whole the entire way.
 *
 * Only transforms change while it runs; the copies are built once, before the
 * first frame, and taken away at the end. The element itself is hidden for the
 * duration (the caller unmounts it afterwards).
 */
import { cubicBezier } from '@shared/motion';

export interface GenieOptions {
  /** ms, 680 by default. */
  duration?: number;
  /** Half-width of the neck the element pours through, in px. */
  neck?: number;
  /** z-index of the layer that carries the strips. */
  zIndex?: number;
  /** Runs once per frame with the overall progress 0..1 (e.g. a backdrop fade). */
  onProgress?: (t: number) => void;
}

// Each band eases off its spot and glides into the target...
const travel = cubicBezier(0.55, 0, 0.4, 1);
// ...and narrows ahead of its travel, which is what draws the funnel.
const narrow = cubicBezier(0.25, 0, 0.2, 1);
// Share of the run the farthest band waits before it sets off.
const STAGGER = 0.48;

/**
 * The CSS matrix3d that maps a w×h box (transform-origin 0 0, placed at the
 * viewport origin) onto the quad TL, TR, BR, BL (Heckbert's square-to-quad,
 * scaled to the box).
 */
const quadMatrix = (w: number, h: number, q: number[]): string => {
  const [x0, y0, x1, y1, x2, y2, x3, y3] = q;
  const dx1 = x1 - x2;
  const dx2 = x3 - x2;
  const dy1 = y1 - y2;
  const dy2 = y3 - y2;
  const sx = x0 - x1 + x2 - x3;
  const sy = y0 - y1 + y2 - y3;
  let g = 0;
  let k = 0;
  const det = dx1 * dy2 - dx2 * dy1;
  if ((Math.abs(sx) > 1e-6 || Math.abs(sy) > 1e-6) && Math.abs(det) > 1e-9) {
    g = (sx * dy2 - dx2 * sy) / det;
    k = (dx1 * sy - sx * dy1) / det;
  }
  const a = x1 - x0 + g * x1;
  const b = x3 - x0 + k * x3;
  const d = y1 - y0 + g * y1;
  const e = y3 - y0 + k * y3;
  return `matrix3d(${a / w},${d / w},0,${g / w},${b / h},${e / h},0,${k / h},0,0,1,0,${x0},${y0},0,1)`;
};

export function genie(el: HTMLElement, target: { x: number; y: number }, options: GenieOptions = {}): Promise<void> {
  const duration = options.duration ?? 680;
  const neck = options.neck ?? 8;
  const { left: L, top: T, width: W, height: H } = el.getBoundingClientRect();
  if (!W || !H) return Promise.resolve();

  const bands = Math.max(14, Math.min(32, Math.round(H / 20)));
  const bandH = H / bands;
  // Each strip carries a little more than its band: the extra slides under the
  // next strip, so the anti-aliased seam between two shows picture, not a gap.
  const EXTRA = 6;
  const boxH = bandH + EXTRA;
  const reach = boxH / bandH;

  // The strips: a clipped copy of the element per band.
  const layer = document.createElement('div');
  layer.className = 'genie-layer';
  layer.setAttribute('aria-hidden', 'true');
  layer.style.cssText = `position:fixed;inset:0;pointer-events:none;z-index:${options.zIndex ?? 115}`;
  const scrolled = Array.from(el.querySelectorAll<HTMLElement>('*'))
    .map((node, i) => [i, node.scrollTop] as const)
    .filter(([, top]) => top > 0);
  const strips: HTMLElement[] = [];
  for (let i = 0; i < bands; i++) {
    const strip = document.createElement('div');
    strip.style.cssText = `position:absolute;left:0;top:0;width:${W}px;height:${boxH}px;overflow:hidden;transform-origin:0 0;will-change:transform;backface-visibility:hidden`;
    const copy = el.cloneNode(true) as HTMLElement;
    copy.removeAttribute('id');
    copy.querySelectorAll('[id]').forEach((node) => node.removeAttribute('id'));
    copy.classList.add('genie-copy');
    copy.style.cssText += `;position:absolute;left:0;top:${-i * bandH}px;width:${W}px;height:${H}px;max-width:none;max-height:none;margin:0;transform:none;opacity:1;box-shadow:none`;
    strip.appendChild(copy);
    layer.appendChild(strip);
    strips.push(strip);
  }
  document.body.appendChild(layer);
  // Inner scroll positions (a sheet scrolled on a small phone) carry over.
  if (scrolled.length) {
    for (const strip of strips) {
      const nodes = strip.firstElementChild!.querySelectorAll<HTMLElement>('*');
      for (const [i, top] of scrolled) if (nodes[i]) nodes[i].scrollTop = top;
    }
  }
  el.style.visibility = 'hidden';

  // Every band edge is a row: where it is and how wide it is at time t.
  const rows = bands + 1;
  const rowY = Array.from({ length: rows }, (_, j) => T + j * bandH);
  const far = Math.max(...rowY.map((y) => Math.abs(y - target.y))) || 1;
  const delay = rowY.map((y) => (Math.abs(y - target.y) / far) * STAGGER);
  const ys = new Float64Array(rows);
  const ls = new Float64Array(rows);
  const rs = new Float64Array(rows);

  return new Promise((resolve) => {
    let start = -1;
    const frame = (now: number) => {
      if (start < 0) start = now;
      const t = Math.min(1, (now - start) / duration);
      for (let j = 0; j < rows; j++) {
        const p = Math.min(1, Math.max(0, (t - delay[j]) / (1 - STAGGER)));
        const n = narrow(Math.min(1, p * 1.25));
        ys[j] = rowY[j] + (target.y - rowY[j]) * travel(p);
        ls[j] = L + (target.x - neck - L) * n;
        rs[j] = L + W + (target.x + neck - L - W) * n;
      }
      for (let i = 0; i < bands; i++) {
        const strip = strips[i];
        const top = ys[i];
        if (ys[i + 1] - top < 0.5) {
          strip.style.visibility = 'hidden';
          continue;
        }
        strip.style.visibility = '';
        // The box's bottom edge lies `reach` of the way along the band's sides.
        const bottom = top + (ys[i + 1] - top) * reach;
        const bl = ls[i] + (ls[i + 1] - ls[i]) * reach;
        const br = rs[i] + (rs[i + 1] - rs[i]) * reach;
        strip.style.transform = quadMatrix(W, boxH, [ls[i], top, rs[i], top, br, bottom, bl, bottom]);
      }
      // The last of it fades as it reaches the neck.
      layer.style.opacity = t > 0.86 ? String(Math.max(0, 1 - (t - 0.86) / 0.14)) : '1';
      options.onProgress?.(t);
      if (t < 1) {
        requestAnimationFrame(frame);
      } else {
        layer.remove();
        resolve();
      }
    };
    requestAnimationFrame(frame);
  });
}
