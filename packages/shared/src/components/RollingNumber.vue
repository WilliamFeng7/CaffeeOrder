<script setup lang="ts">
/**
 * A small count (cart badge, quantity stepper, column count) whose value rolls
 * like an odometer when it changes: up when it grows, down when it shrinks.
 * Old and new value share one grid cell, so nothing needs absolute positioning.
 * CSS transitions (motion.css .roll-*), so fast repeated taps retarget.
 */
import { ref, watch } from 'vue';

const props = defineProps<{ value: number }>();

const direction = ref<'up' | 'down'>('up');
watch(() => props.value, (next, prev) => {
  direction.value = next >= prev ? 'up' : 'down';
});
</script>

<template>
  <span class="relative inline-grid overflow-hidden tabular-nums">
    <Transition :name="`roll-${direction}`">
      <span :key="value" class="col-start-1 row-start-1">{{ value }}</span>
    </Transition>
  </span>
</template>
