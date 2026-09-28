<script setup lang="ts">
/**
 * AppIcon.vue (Student)
 *
 * 超简约线条图标 (Ultra-minimal line icons): one to three strokes, one stroke
 * weight, round ends (paths in src/icons.ts). Sized by the surrounding font
 * size (1em) and coloured by `currentColor`, the same contract as the shared
 * icon, so templates only change their import.
 *
 *   <AppIcon name="coffee" />                  1.5px line
 *   <AppIcon name="coffee" weight="fill" />    selected: a touch heavier
 *   <AppIcon name="check" draw />              strokes trace in, one after another
 *
 * `draw` plays when the icon is created; re-key it to play again.
 */
import { computed } from 'vue';
import { ICONS, type IconName, type IconWeight } from '@/icons';

const props = withDefaults(defineProps<{
  name: IconName;
  weight?: IconWeight;
  size?: string | number;
  label?: string;
  /** Trace the strokes in when created (a line being drawn). */
  draw?: boolean;
}>(), {
  weight: 'regular',
  size: '1em',
  label: undefined,
  draw: false,
});

const STROKE: Record<IconWeight, number> = { light: 1.25, regular: 1.5, fill: 1.9, bold: 1.9 };
const strokeWidth = computed(() => STROKE[props.weight]);
const paths = computed(() => ICONS[props.name] ?? []);
</script>

<template>
  <svg
    class="app-icon"
    :class="{ 'is-drawing': draw }"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    :width="size"
    :height="size"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    focusable="false"
    :role="label ? 'img' : undefined"
    :aria-label="label"
    :aria-hidden="label ? undefined : 'true'"
  >
    <path
      v-for="(d, i) in paths"
      :key="i"
      :d="d"
      pathLength="1"
      :style="draw ? { animationDelay: `${i * 90}ms` } : undefined"
    />
  </svg>
</template>

<style>
/* Unscoped on purpose: the defaults sit in :where() (zero specificity), so a
   size or display utility on the icon still wins; without one an icon is 24px. */
:where(.app-icon) {
  display: inline-block;
  flex-shrink: 0;
  vertical-align: -0.125em;
  font-size: 1.5rem;
}

.app-icon {
  box-sizing: content-box;
  overflow: visible;
  transition: stroke-width var(--dur-color) var(--ease-out);
}

/* The stroke is drawn from its start to its end (pathLength = 1), each path a
   beat after the previous one. */
.app-icon.is-drawing path {
  stroke-dasharray: 1 1;
  stroke-dashoffset: 1;
  animation: iconDraw var(--dur-enter) var(--ease-out) forwards;
}

@keyframes iconDraw {
  to {
    stroke-dashoffset: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-icon.is-drawing path {
    animation: none;
    stroke-dashoffset: 0;
  }
}
</style>
