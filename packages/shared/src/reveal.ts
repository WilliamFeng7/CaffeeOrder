/**
 * v-reveal: the element rises and fades into place the first time it scrolls
 * into view - once, not every time. `v-reveal="120"` delays it by 120ms, for a
 * hand-made stagger across sections. Elements already on screen when mounted
 * reveal straight away, so a page's first paint still plays in order.
 *
 * Styles live in styles/motion.css (.reveal / .is-revealed). When the reveal is
 * over the classes are removed again, so the element's own transitions (press,
 * hover) are untouched afterwards. Register per app:
 *   app.directive('reveal', vReveal)
 */
import type { Directive } from 'vue';
import { motionMs } from './motion';

const done = (el: HTMLElement, delay: number) => {
  el.classList.add('is-revealed');
  window.setTimeout(() => {
    el.classList.remove('reveal', 'is-revealed');
    el.style.removeProperty('--reveal-delay');
  }, delay + motionMs('--dur-enter', 560) + 60);
};

let observer: IntersectionObserver | null = null;
const delays = new WeakMap<Element, number>();

const getObserver = () => {
  if (observer || typeof IntersectionObserver === 'undefined') return observer;
  observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      observer?.unobserve(entry.target);
      done(entry.target as HTMLElement, delays.get(entry.target) ?? 0);
    }
  }, { rootMargin: '0px 0px -6% 0px', threshold: 0.01 });
  return observer;
};

export const vReveal: Directive<HTMLElement, number | undefined> = {
  mounted(el, { value }) {
    const io = getObserver();
    if (!io) return;
    const delay = value ?? 0;
    delays.set(el, delay);
    if (delay) el.style.setProperty('--reveal-delay', `${delay}ms`);
    el.classList.add('reveal');
    io.observe(el);
  },
  beforeUnmount(el) {
    observer?.unobserve(el);
  },
};
