/**
 * useKeepScroll.ts
 *
 * 切换标签页后回到原来的滚动位置 (Keep a tab's scroll position).
 * The tabs are cached by <KeepAlive>, but a scroll container that is taken out
 * of the page loses its offset, so it is recorded while scrolling and put back
 * when the tab is shown again.
 *
 * Usage: `const { scroller, onScroll } = useKeepScroll();` and
 * `<main ref="scroller" @scroll.passive="onScroll">`.
 */
import { ref, onActivated } from 'vue';

export function useKeepScroll() {
  const scroller = ref<HTMLElement | null>(null);
  let top = 0;

  const onScroll = () => {
    top = scroller.value?.scrollTop ?? 0;
  };

  onActivated(() => {
    if (scroller.value && top) scroller.value.scrollTop = top;
  });

  return { scroller, onScroll };
}
