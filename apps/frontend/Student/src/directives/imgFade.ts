/**
 * v-img-fade
 *
 * 图片加载完成后淡入 (A photo fades in once it has loaded) instead of popping
 * in half-way through a scroll or an animation. Images that are already
 * loaded (cached) show at once. Opacity only: no scale, so a page full of
 * photos does not turn into a page full of animating layers.
 *
 *   <img v-img-fade :src="p.thumb" :data-full="p.image">
 *
 * `data-full`: if the small file fails to load, the full-size one is used.
 * Styles: .img-fade / .img-loading in src/index.css.
 */
import type { Directive } from 'vue';

const watchLoad = (el: HTMLImageElement) => {
  el.dataset.fadeSrc = el.getAttribute('src') ?? '';
  el.classList.add('img-fade');
  if (el.complete && el.naturalWidth > 0) {
    el.classList.remove('img-loading');
    return;
  }
  el.classList.add('img-loading');
  const done = () => {
    el.removeEventListener('load', done);
    el.removeEventListener('error', failed);
    el.classList.remove('img-loading');
  };
  const failed = () => {
    const full = el.dataset.full;
    if (full && el.getAttribute('src') !== full) {
      el.setAttribute('src', full);
      el.dataset.fadeSrc = full;
      return; // still listening: the full one fades in when it loads
    }
    done();
  };
  el.addEventListener('load', done);
  el.addEventListener('error', failed);
};

export const vImgFade: Directive<HTMLImageElement, unknown> = {
  mounted(el) {
    watchLoad(el);
  },
  updated(el) {
    // A reused <img> that was given another picture fades that one in too.
    if (el.dataset.fadeSrc !== (el.getAttribute('src') ?? '')) watchLoad(el);
  },
};
