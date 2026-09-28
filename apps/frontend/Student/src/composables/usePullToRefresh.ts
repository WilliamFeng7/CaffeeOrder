/**
 * usePullToRefresh.ts
 *
 * 下拉刷新 (Pull to refresh) for a scroll area that is at its top. The content
 * follows the finger with rising resistance; past the threshold it holds
 * while `refresh()` runs and a line spinner turns, then springs home.
 *
 * Touch events (not pointer events) because the pull has to stop the
 * browser's own overscroll with preventDefault; a gesture that is mostly
 * sideways is left alone, so a horizontal pager on the same area still works.
 * The styles are written directly to the elements each frame (no re-render).
 */
import { ref, onMounted, onBeforeUnmount, type Ref } from 'vue';
import { spring, rubberband, type SpringHandle } from './spring';

const THRESHOLD = 64; // px of pull that triggers a refresh
const HOLD = 56;      // where the content rests while refreshing

export function usePullToRefresh(
  scroller: Ref<HTMLElement | null>,
  content: Ref<HTMLElement | null>,
  indicator: Ref<HTMLElement | null>,
  refresh: () => Promise<unknown>,
) {
  const refreshing = ref(false);
  let startX = 0;
  let startY = 0;
  let armed = false;
  let pulling = false;
  let distance = 0;
  let anim: SpringHandle | null = null;

  const paint = (d: number) => {
    distance = d;
    if (content.value) content.value.style.transform = d ? `translate3d(0, ${d}px, 0)` : '';
    const el = indicator.value;
    if (!el) return;
    const p = Math.min(1, d / THRESHOLD);
    el.style.opacity = String(p);
    el.style.transform = `translate3d(-50%, ${d / 2 - 12}px, 0) rotate(${p * 270}deg) scale(${0.6 + p * 0.4})`;
    // The ring closes as the pull approaches the threshold.
    const arc = el.querySelector<SVGElement>('circle');
    if (arc && !refreshing.value) arc.style.strokeDashoffset = String(1 - p * 0.85);
  };

  const settle = (to: number, velocity = 0, done?: () => void) => {
    anim?.stop();
    anim = spring(distance, to, { response: 0.4, dampingRatio: 1, velocity, onUpdate: paint, onComplete: done });
  };

  const onStart = (e: TouchEvent) => {
    const el = scroller.value;
    if (!el || refreshing.value || e.touches.length !== 1) return;
    armed = el.scrollTop <= 0;
    pulling = false;
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
  };

  const onMove = (e: TouchEvent) => {
    if (!armed) return;
    const dx = e.touches[0].clientX - startX;
    const dy = e.touches[0].clientY - startY;
    if (!pulling) {
      // Up (a scroll) or sideways (the pager): not a pull.
      if (dy <= 0 || Math.abs(dx) > dy) {
        if (dy < -4 || Math.abs(dx) > 8) armed = false;
        return;
      }
      pulling = true;
      anim?.stop();
    } else if (Math.abs(dx) > Math.max(24, dy)) {
      // It turned into a sideways swipe: hand it to the pager.
      armed = false;
      pulling = false;
      settle(0);
      return;
    }
    // Decided on the first move, before Safari starts its own overscroll.
    if (e.cancelable) e.preventDefault();
    paint(dy > 0 ? rubberband(dy, 260) : 0);
  };

  const onEnd = () => {
    if (!armed || !pulling) {
      armed = false;
      return;
    }
    armed = false;
    pulling = false;
    if (distance < THRESHOLD) {
      settle(0);
      return;
    }
    refreshing.value = true;
    settle(HOLD);
    const started = performance.now();
    void refresh().finally(() => {
      // Spin at least a little, so a fast response doesn't flicker.
      const wait = Math.max(0, 600 - (performance.now() - started));
      window.setTimeout(() => settle(0, 0, () => { refreshing.value = false; }), wait);
    });
  };

  onMounted(() => {
    const el = scroller.value;
    if (!el) return;
    el.addEventListener('touchstart', onStart, { passive: true });
    el.addEventListener('touchmove', onMove, { passive: false });
    el.addEventListener('touchend', onEnd, { passive: true });
    el.addEventListener('touchcancel', onEnd, { passive: true });
  });

  onBeforeUnmount(() => {
    anim?.stop();
    const el = scroller.value;
    if (!el) return;
    el.removeEventListener('touchstart', onStart);
    el.removeEventListener('touchmove', onMove);
    el.removeEventListener('touchend', onEnd);
    el.removeEventListener('touchcancel', onEnd);
  });

  return { refreshing };
}
