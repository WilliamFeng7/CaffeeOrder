<script setup lang="ts">
/**
 * A number that counts to its new value instead of jumping: KPIs, totals,
 * balances. It counts up from zero the first time it is shown, then from
 * whatever it currently shows (so a change mid-count retargets smoothly).
 * Tabular figures keep the digits from shuffling sideways while they count.
 * Under reduced motion the value is simply replaced.
 *
 *   <AnimatedNumber :value="revenue" :format="n => `¥${n.toFixed(2)}`" />
 */
import { ref, watch, onBeforeUnmount } from 'vue';
import { easeOut, motionMs, prefersReducedMotion } from '../motion';

const props = withDefaults(defineProps<{
  value: number;
  /** Formats every frame's value; defaults to a rounded integer. */
  format?: (n: number) => string;
  /** Count up from 0 when first shown (default), or start at the value. */
  fromZero?: boolean;
}>(), {
  format: (n: number) => String(Math.round(n)),
  fromZero: true,
});

const shown = ref(props.fromZero ? 0 : props.value);
let frame = 0;

const run = (to: number) => {
  cancelAnimationFrame(frame);
  const from = shown.value;
  if (!Number.isFinite(to)) {
    shown.value = 0;
    return;
  }
  if (from === to || prefersReducedMotion()) {
    shown.value = to;
    return;
  }
  const duration = motionMs('--dur-count', 900);
  // Timed from the first frame's own timestamp, so the clock is always the
  // one requestAnimationFrame reports.
  let start = -1;
  const step = (now: number) => {
    if (start < 0) start = now;
    const p = Math.min(1, (now - start) / duration);
    shown.value = p === 1 ? to : from + (to - from) * easeOut(p);
    if (p < 1) frame = requestAnimationFrame(step);
  };
  frame = requestAnimationFrame(step);
};

watch(() => props.value, run, { immediate: true });
onBeforeUnmount(() => cancelAnimationFrame(frame));
</script>

<template>
  <span class="tabular-nums">{{ format(shown) }}</span>
</template>
