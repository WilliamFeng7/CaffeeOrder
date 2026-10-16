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
 *
 * Icons do not animate their strokes: a line being traced in repaints the SVG
 * every frame and read as flicker on tabs that change all the time.
 */
import { computed } from 'vue';
import { ICONS, type IconName, type IconWeight } from '@/icons';

const props = withDefaults(defineProps<{
  name: IconName;
  weight?: IconWeight;
  size?: string | number;
  label?: string;
}>(), {
  weight: 'regular',
  size: '1em',
  label: undefined,
});

const STROKE: Record<IconWeight, number> = { light: 1.25, regular: 1.5, fill: 1.9, bold: 1.9 };
const strokeWidth = computed(() => STROKE[props.weight]);
const paths = computed(() => ICONS[props.name] ?? []);
</script>

<template>
  <svg
    class="app-icon"
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

</style>
