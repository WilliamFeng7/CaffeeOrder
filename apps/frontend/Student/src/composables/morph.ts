/**
 * morph.ts
 *
 * 共享元素过渡 (Shared-element transitions): the tapped product photo grows out
 * of its card into the product sheet and shrinks back into it on close; an
 * item added to the cart flies from the sheet into the cart bar.
 *
 * Built on the View Transitions API (Safari / iPadOS 18, Chrome 111+): the
 * browser morphs the photo's box between its old and new place, so nothing is
 * measured by hand. Where the API is missing, or reduced motion is on, the
 * update just runs and the sheet's own CSS entrance / exit plays instead.
 * The per-kind choreography (what fades, how long the flight takes) is in
 * index.css under html[data-morph].
 */
import { nextTick } from 'vue';

export type MorphKind = 'open' | 'close' | 'cart';

const NAME = 'product-hero';

type StartViewTransition = (update: () => Promise<void>) => { finished: Promise<void>; skipTransition(): void };

const startViewTransition = (): StartViewTransition | null => {
  const fn = (document as Document & { startViewTransition?: StartViewTransition }).startViewTransition;
  return typeof fn === 'function' ? fn.bind(document) : null;
};

export const canMorph = (): boolean =>
  typeof document !== 'undefined'
  && startViewTransition() !== null
  && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/** Rendered and at least partly inside the viewport. */
export const onScreen = (el: Element | null | undefined): el is HTMLElement => {
  if (!el || !el.isConnected) return false;
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0 && r.bottom > 0 && r.right > 0
    && r.top < window.innerHeight && r.left < window.innerWidth;
};

let current: { skipTransition(): void } | null = null;

/**
 * Runs `update` so that `from` (in the current DOM) turns into whatever `to`
 * returns once the update has rendered. Resolves when the animation is over;
 * returns false when it ran without one.
 */
export async function morph(
  kind: MorphKind,
  from: HTMLElement | null | undefined,
  update: () => void,
  to: () => HTMLElement | null | undefined,
): Promise<boolean> {
  const start = startViewTransition();
  if (!start || !canMorph() || !onScreen(from)) {
    update();
    return false;
  }

  current?.skipTransition();
  const root = document.documentElement;
  root.dataset.morph = kind;
  from.style.setProperty('view-transition-name', NAME);
  let target: HTMLElement | null = null;

  const transition = start(async () => {
    from.style.removeProperty('view-transition-name');
    update();
    await nextTick();
    const el = to();
    if (!onScreen(el)) return;
    target = el;
    el.style.setProperty('view-transition-name', NAME);
    // Same URL as the card, so this is normally instant; never wait long.
    if (el instanceof HTMLImageElement && !el.complete) {
      await Promise.race([el.decode().catch(() => undefined), new Promise(r => setTimeout(r, 120))]);
    }
  });
  current = transition;

  try {
    await transition.finished;
  } catch {
    // Skipped by a newer morph: the DOM is already in its final state.
  } finally {
    (target as HTMLElement | null)?.style.removeProperty('view-transition-name');
    if (current === transition) {
      current = null;
      delete root.dataset.morph;
    }
  }
  return true;
}
