/**
 * useKeyboardInset.ts
 *
 * 屏幕键盘遮挡了多少 (How much of the screen the on-screen keyboard covers).
 * iPadOS / iOS shrink the *visual* viewport when the keyboard opens but leave
 * `position: fixed` layouts where they were, so a sheet at the bottom of the
 * screen (or in the middle of an iPad) ends up behind the keyboard with the
 * field being typed into. Pad the sheet's container by this many pixels.
 */
import { ref, watch, onBeforeUnmount, type Ref } from 'vue';

export function useKeyboardInset(active: Ref<boolean>) {
  const inset = ref(0);
  const vv = typeof window !== 'undefined' ? window.visualViewport : null;

  const update = () => {
    if (!vv) return;
    const covered = window.innerHeight - vv.height - vv.offsetTop;
    // Small differences are browser chrome, not a keyboard.
    inset.value = covered > 80 ? Math.round(covered) : 0;
  };

  const start = () => {
    if (!vv) return;
    vv.addEventListener('resize', update);
    vv.addEventListener('scroll', update);
    update();
  };

  const stop = () => {
    if (!vv) return;
    vv.removeEventListener('resize', update);
    vv.removeEventListener('scroll', update);
    inset.value = 0;
  };

  watch(active, (on) => (on ? start() : stop()), { immediate: true });
  onBeforeUnmount(stop);

  return inset;
}
