/**
 * Helpers for <TransitionGroup name="list">.
 *
 * The shared .list-leave-active takes a leaving item out of flow
 * (position: absolute) so the others can glide into its place. In a
 * single-column list it spans the row (left/right 0); in a grid that would
 * stretch a card across the whole grid, so pin it to its current box first:
 *   <TransitionGroup name="list" @before-leave="pinLeaving">
 */
export function pinLeaving(el: Element): void {
  const e = el as HTMLElement;
  e.style.width = `${e.offsetWidth}px`;
  e.style.height = `${e.offsetHeight}px`;
  e.style.left = `${e.offsetLeft}px`;
  e.style.top = `${e.offsetTop}px`;
}
