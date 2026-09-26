/**
 * useSheetDrag.ts
 *
 * 下拉关闭面板 (Swipe down to dismiss) — the gesture iPad and iPhone users try
 * first on any sheet. The handle element receives the pointer listeners (give
 * it `touch-none` so the browser does not scroll instead); the sheet element is
 * what moves.
 *
 * While the finger is down the sheet follows it 1:1 (upwards it meets rising
 * resistance). On release it either continues off-screen and calls `onDismiss`,
 * or settles back. It dismisses on distance or on a flick, so a short fast
 * swipe works as well as a long slow one.
 */
import { ref, onBeforeUnmount, type Ref } from 'vue';

interface SheetDragOptions {
  sheet: Ref<HTMLElement | null>;
  backdrop?: Ref<HTMLElement | null>;
  onDismiss: () => void;
}

const DISMISS_DISTANCE = 120; // px (or a quarter of a short sheet)
// px per ms, averaged over the drag. Sheet-sized: a slow, hesitant nudge
// settles back instead of closing.
const DISMISS_VELOCITY = 0.4;
const DRAWER_EASE = 'cubic-bezier(0.32, 0.72, 0, 1)';
const SETTLE_MS = 300;
const EXIT_MS = 220;

// iOS-style rubber band: the further past the edge, the less it moves.
const rubberBand = (distance: number, dimension = 200) =>
  (1 - 1 / ((distance * 0.55) / dimension + 1)) * dimension;

const prefersReducedMotion = () =>
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export function useSheetDrag({ sheet, backdrop, onDismiss }: SheetDragOptions) {
  const dragging = ref(false);
  let pointerId: number | null = null;
  let startY = 0;
  let startTime = 0;
  let offset = 0;
  let settleTimer: number | undefined;
  let exitTimer: number | undefined;

  const place = (y: number) => {
    const el = sheet.value;
    if (!el) return;
    el.style.transform = `translate3d(0, ${y}px, 0)`;
    const bd = backdrop?.value;
    if (bd) bd.style.opacity = String(y > 0 ? Math.max(0, 1 - y / el.offsetHeight) : 1);
  };

  const setTransition = (sheetValue: string, backdropValue: string) => {
    if (sheet.value) sheet.value.style.transition = sheetValue;
    if (backdrop?.value) backdrop.value.style.transition = backdropValue;
  };

  const onPointerDown = (e: PointerEvent) => {
    // A second finger must not take over (the sheet would jump to it).
    if (pointerId !== null) return;
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    // Controls inside the handle keep working as taps.
    if ((e.target as HTMLElement).closest('button, a, input, textarea, select')) return;
    pointerId = e.pointerId;
    startY = e.clientY;
    startTime = performance.now();
    offset = 0;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  };

  const onPointerMove = (e: PointerEvent) => {
    if (e.pointerId !== pointerId) return;
    const raw = e.clientY - startY;
    if (!dragging.value) {
      if (Math.abs(raw) < 6) return; // a tap is not a drag
      dragging.value = true;
      window.clearTimeout(settleTimer);
      setTransition('none', 'none');
    }
    offset = raw >= 0 ? raw : -rubberBand(-raw);
    place(offset);
  };

  const finish = (e: PointerEvent) => {
    if (e.pointerId !== pointerId) return;
    pointerId = null;
    if (!dragging.value) return;
    dragging.value = false;

    const el = sheet.value;
    if (!el) return;
    const velocity = offset / Math.max(1, performance.now() - startTime);
    const distance = Math.min(DISMISS_DISTANCE, el.offsetHeight * 0.25);
    const dismiss = e.type === 'pointerup'
      && (offset > distance || (offset > 16 && velocity > DISMISS_VELOCITY));

    if (dismiss) {
      // Carry on in the direction of the swipe, from where the finger let go.
      const exit = prefersReducedMotion() ? 0 : EXIT_MS;
      setTransition(`transform ${exit}ms ${DRAWER_EASE}`, `opacity ${exit}ms ease-out`);
      el.style.transform = `translate3d(0, ${window.innerHeight}px, 0)`;
      if (backdrop?.value) backdrop.value.style.opacity = '0';
      exitTimer = window.setTimeout(onDismiss, exit);
      return;
    }

    setTransition(`transform ${SETTLE_MS}ms ${DRAWER_EASE}`, `opacity ${SETTLE_MS}ms ease-out`);
    el.style.transform = '';
    if (backdrop?.value) backdrop.value.style.opacity = '';
    // Hand the transitions back to the component's own classes.
    settleTimer = window.setTimeout(() => setTransition('', ''), SETTLE_MS);
  };

  onBeforeUnmount(() => {
    window.clearTimeout(settleTimer);
    window.clearTimeout(exitTimer);
  });

  return {
    dragging,
    /** Spread onto the handle with v-on. */
    handlers: {
      pointerdown: onPointerDown,
      pointermove: onPointerMove,
      pointerup: finish,
      pointercancel: finish,
    },
  };
}
