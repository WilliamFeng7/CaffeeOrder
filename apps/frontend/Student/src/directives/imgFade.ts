/**
 * v-img-fade
 *
 * 图片加载完成后淡入 (A photo fades in once it has decoded) and settles from a
 * slight zoom, instead of popping in half-way through a scroll or an
 * animation. Images that are already decoded (cached) show at once, so a
 * shared-element morph always has a picture to capture.
 *
 *   <img v-img-fade :src="…">        fade + settle from 103%
 *   <img v-img-fade:hero :src="…">   the featured photo: a slower settle from 108%
 *
 * Styles: .img-fade / .img-loading / .hero-settle in src/index.css.
 */
import type { Directive } from 'vue';

const watchLoad = (el: HTMLImageElement, hero: boolean) => {
  el.dataset.fadeSrc = el.getAttribute('src') ?? '';
  el.classList.add('img-fade');
  if (el.complete) {
    el.classList.remove('img-loading');
    if (hero) el.classList.add('hero-settle');
    return;
  }
  el.classList.add('img-loading');
  const done = () => {
    el.removeEventListener('load', done);
    el.removeEventListener('error', done);
    el.classList.remove('img-loading');
    if (hero) el.classList.add('hero-settle');
  };
  el.addEventListener('load', done);
  el.addEventListener('error', done);
};

export const vImgFade: Directive<HTMLImageElement, unknown> = {
  mounted(el, binding) {
    watchLoad(el, binding.arg === 'hero');
  },
  updated(el, binding) {
    // A reused <img> that was given another picture fades that one in too.
    if (el.dataset.fadeSrc !== (el.getAttribute('src') ?? '')) {
      el.classList.remove('hero-settle');
      watchLoad(el, binding.arg === 'hero');
    }
  },
};
