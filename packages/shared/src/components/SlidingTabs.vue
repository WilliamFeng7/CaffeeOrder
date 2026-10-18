<script setup lang="ts" generic="T extends string | number">
/**
 * Text tabs or a segmented control with one indicator that glides to the
 * selected option on a spring. The indicator moves with transform only
 * (translateX, plus scaleX for the underline) from the measured button
 * positions, so labels of any width work; it re-measures on resize and when
 * the labels change (language switch).
 *
 *   <SlidingTabs v-model="filter" :options="[{ value: 'all', label: '全部' }, …]" />
 *   <SlidingTabs v-model="tab" :options="…" variant="segment" stretch />
 *
 * Touch: size "lg" gives 44px+ segments for iPad; underline tabs sit edge to
 * edge (padding, not gaps), so a tap between two labels still hits one.
 */
import { ref, watch, computed, nextTick, onMounted, onActivated, onBeforeUnmount } from 'vue';

const props = withDefaults(defineProps<{
  modelValue: T;
  options: { value: T; label: string }[];
  variant?: 'underline' | 'segment';
  size?: 'sm' | 'md' | 'lg';
  /** Equal-width options filling the container. */
  stretch?: boolean;
  /** Accessible name of the group. */
  label?: string;
}>(), {
  variant: 'underline',
  size: 'md',
  stretch: false,
  label: undefined,
});

const emit = defineEmits<{ (e: 'update:modelValue', value: T): void }>();

const track = ref<HTMLElement | null>(null);
const buttons: HTMLElement[] = [];
const pos = ref({ x: 0, w: 0 });
// The first placement must not slide in from the left edge.
const settled = ref(false);

const activeIndex = computed(() => props.options.findIndex(o => o.value === props.modelValue));

const measure = () => {
  const el = buttons[activeIndex.value];
  if (!el || !el.offsetWidth) return;
  if (props.variant === 'underline') {
    // The line sits under the label; the padding around it is hit area only.
    const label = el.firstElementChild as HTMLElement | null;
    const x = el.offsetLeft + (label?.offsetLeft ?? 0);
    pos.value = { x, w: label?.offsetWidth ?? el.offsetWidth };
    return;
  }
  pos.value = { x: el.offsetLeft, w: el.offsetWidth };
};

const select = (value: T, i: number) => {
  emit('update:modelValue', value);
  // Keep the chosen tab in view when the row scrolls sideways (phones).
  const el = buttons[i];
  const row = track.value?.parentElement;
  if (el && row && row.scrollWidth > row.clientWidth) {
    row.scrollTo({ left: el.offsetLeft - (row.clientWidth - el.offsetWidth) / 2, behavior: 'smooth' });
  }
};

const onKey = (e: KeyboardEvent) => {
  if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
  e.preventDefault();
  const n = props.options.length;
  const i = (Math.max(0, activeIndex.value) + (e.key === 'ArrowRight' ? 1 : n - 1)) % n;
  select(props.options[i].value, i);
  void nextTick(() => buttons[i]?.focus());
};

watch(activeIndex, () => nextTick(measure));
watch(() => props.options.map(o => o.label).join('\u0000'), () => nextTick(measure));

let observer: ResizeObserver | null = null;
onMounted(() => {
  measure();
  requestAnimationFrame(() => { settled.value = true; });
  if (typeof ResizeObserver !== 'undefined' && track.value) {
    observer = new ResizeObserver(() => measure());
    observer.observe(track.value);
  }
  void document.fonts?.ready.then(measure);
});
// Inside a <KeepAlive> tab the row was detached (zero size) while hidden.
onActivated(measure);
onBeforeUnmount(() => observer?.disconnect());

const sizeClass = computed(() => {
  if (props.variant === 'segment') {
    return {
      sm: 'h-8 px-3.5 text-[13px] rounded-full',
      md: 'h-9 px-4 text-[14px] rounded-full',
      lg: 'h-11 px-5 text-[15px] rounded-full',
    }[props.size];
  }
  // Neighbouring underline tabs touch (padding instead of a gap).
  return {
    sm: 'h-10 px-2.5 text-[13px]',
    md: 'h-12 px-3 text-[15px]',
    lg: 'h-14 px-4 text-[16px]',
  }[props.size];
});
</script>

<template>
  <div
    ref="track"
    role="tablist"
    :aria-label="label"
    class="relative"
    :class="[
      stretch ? 'grid' : 'inline-flex',
      variant === 'segment' ? 'p-1 rounded-full bg-cream' : '',
    ]"
    :style="stretch ? { gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` } : undefined"
    @keydown="onKey"
  >
    <span
      aria-hidden="true"
      class="sliding-indicator absolute left-0 pointer-events-none"
      :class="[
        variant === 'segment' ? 'top-1 bottom-1 rounded-full bg-surface-light shadow-card' : 'bottom-0 h-[2px] w-px bg-text-main',
        { 'is-settling': !settled },
      ]"
      :style="variant === 'segment'
        ? { width: `${pos.w}px`, transform: `translate3d(${pos.x}px, 0, 0)` }
        : { transform: `translate3d(${pos.x}px, 0, 0) scaleX(${pos.w})` }"
    ></span>
    <button
      v-for="(o, i) in options"
      :key="String(o.value)"
      :ref="el => { if (el) buttons[i] = el as HTMLElement }"
      type="button"
      role="tab"
      :aria-selected="o.value === modelValue"
      :tabindex="o.value === modelValue ? 0 : -1"
      class="relative z-10 whitespace-nowrap"
      :class="[sizeClass, o.value === modelValue ? 'text-text-main font-medium' : 'text-text-sub hover:text-text-main']"
      @click="select(o.value, i)"
    ><span class="pointer-events-none">{{ o.label }}</span></button>
  </div>
</template>

<style scoped>
/* Springs between options; the underline also stretches to the new label's
   width (scaleX of a 1px bar), so only transform ever animates. */
.sliding-indicator {
  transform-origin: left center;
  transition: transform var(--dur-spring) var(--ease-spring);
}

.is-settling {
  transition: none;
}

@media (pointer: coarse) {
  button {
    min-block-size: var(--touch-target, 44px);
  }
}
</style>
