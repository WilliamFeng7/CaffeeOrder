<script setup lang="ts">
/**
 * PriceTag.vue
 *
 * 价签 (A large price, set like a menu board): a small raised ¥, the yuan in
 * the display face, and the cents (raised, small) only when there are any.
 * Screen readers get the plain amount.
 */
import { computed } from 'vue';
import { toCents, formatCents } from '../utils/money';

const props = defineProps<{ value: number }>();

const cents = computed(() => toCents(props.value));
const yuan = computed(() => Math.floor(cents.value / 100).toLocaleString('en-US'));
const rest = computed(() => cents.value % 100);
</script>

<template>
  <span class="inline-flex items-start leading-none tabular-nums">
    <span class="sr-only">¥{{ formatCents(cents) }}</span>
    <span class="text-[0.52em] mt-[0.12em] mr-[0.08em]" aria-hidden="true">¥</span>
    <span aria-hidden="true">{{ yuan }}</span>
    <span v-if="rest" class="text-[0.52em] mt-[0.12em] ml-[0.04em]" aria-hidden="true">.{{ String(rest).padStart(2, '0') }}</span>
  </span>
</template>
