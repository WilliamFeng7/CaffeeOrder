<script setup lang="ts">
/**
 * OrderCard.vue
 *
 * One order on the kitchen board: the pickup number the customer holds, how
 * long it has waited, what to make, and the one next action. Late orders get
 * a thin red edge and red wait time instead of alarm badges.
 */
import AppIcon from '@shared/components/AppIcon.vue';
import type { Order } from '../api';
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  order: Order;
  globalTick?: number; // Parent provides this to trigger time recalculation
  /** Arrived after the board loaded: flash once. */
  fresh?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update-status', orderId: number, status: string): void;
}>();

// Time elapsed - computed, re-evaluated on the parent's globalTick
// (one timer for the board instead of one per card).
const timeElapsed = computed(() => {
  void props.globalTick;
  const totalSec = Math.floor((Date.now() - new Date(props.order.created_at).getTime()) / 1000);
  const min = Math.floor(totalSec / 60);
  if (min < 60) {
    return `${min}m`;
  } else if (min >= 24 * 60) {
    // A backlog order from another day reads "3d", not "6309h 3m".
    return `${Math.floor(min / (24 * 60))}d`;
  } else {
    const h = Math.floor(min / 60);
    const m = min % 60;
    return `${h}h${m > 0 ? ` ${m}m` : ''}`;
  }
});

const formatTime = (isoString: string) => {
  return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
};

const waitMinutes = computed(() => {
  void props.globalTick;
  return Math.floor((Date.now() - new Date(props.order.created_at).getTime()) / 60000);
});

const isUrgent = computed(() => {
  // Backend statuses: created / processing / ready / completed / refunded
  if (['ready', 'completed', 'refunded'].includes(props.order.status.toLowerCase())) return false;
  return waitMinutes.value > 10;
});

const nextAction = computed((): { label: string; action: string; primary: boolean } | null => {
  const s = props.order.status.toLowerCase();
  if (s === 'created') return { label: 'Start making', action: 'processing', primary: false };
  if (s === 'processing') return { label: 'Mark ready', action: 'ready', primary: true };
  return null;
});

const itemCount = computed(() => props.order.items.reduce((sum, item) => sum + item.quantity, 0));

// One tap, one status change: the button stays disabled until the order moves
// on (or a few seconds pass, if the update failed), so a double tap cannot
// send the same transition twice.
const pending = ref(false);
let pendingTimer: number | undefined;
watch(() => props.order.status, () => {
  pending.value = false;
  window.clearTimeout(pendingTimer);
});
const runAction = () => {
  if (!nextAction.value || pending.value) return;
  pending.value = true;
  pendingTimer = window.setTimeout(() => { pending.value = false; }, 4000);
  emit('update-status', props.order.id, nextAction.value.action);
};
</script>

<template>
  <article
    class="relative overflow-hidden bg-surface-light rounded-card border p-4 md:p-5 transition-colors duration-fade"
    :class="[isUrgent ? 'border-danger/35' : 'border-line', { flash: fresh }]"
  >
    <span v-if="isUrgent" class="absolute left-0 inset-y-0 w-[3px] bg-danger" aria-hidden="true"></span>

    <!-- Pickup number + wait -->
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <p class="font-serif text-[34px] md:text-[38px] font-medium leading-none tabular-nums" :title="`Order ${order.id}`">
          {{ order.pickup_number ?? order.id }}
        </p>
        <p class="mt-2 text-[12px] tabular-nums text-text-sub">
          {{ formatTime(order.created_at) }}
          <span class="mx-1" aria-hidden="true">·</span>
          <span :class="isUrgent ? 'text-danger font-medium' : ''">{{ timeElapsed }} ago</span>
        </p>
      </div>
      <span class="text-[12px] text-text-sub shrink-0 pt-1">{{ itemCount }} {{ itemCount === 1 ? 'item' : 'items' }}</span>
    </div>

    <!-- What to make -->
    <ul class="mt-4 space-y-2.5">
      <li v-for="(item, i) in order.items" :key="i" class="flex flex-wrap items-center gap-x-2.5 gap-y-1">
        <span class="text-[15px] font-medium tabular-nums">{{ item.quantity }}×</span>
        <span class="text-[15px] flex-1 min-w-[5rem] truncate">{{ item.name }}</span>
        <span class="flex items-center gap-1.5 shrink-0">
          <span
            v-if="item.temperature"
            class="chip"
            :class="item.temperature === 'Hot' ? 'chip-warm' : 'bg-[#E9F1FA] text-[#1F5C99]'"
          >{{ item.temperature }}</span>
          <span v-if="item.sugar" class="chip chip-quiet">{{ item.sugar }}</span>
        </span>
      </li>
    </ul>

    <!-- The one next action -->
    <button
      v-if="nextAction"
      type="button"
      @click="runAction"
      :disabled="pending"
      class="btn w-full mt-5 disabled:!opacity-60"
      :class="nextAction.primary ? 'btn-primary' : 'btn-outline'"
    >
      <span v-if="pending" class="size-4 border-[1.5px] border-current border-r-transparent rounded-full animate-spin" aria-hidden="true"></span>
      <span>{{ nextAction.label }}</span>
    </button>

    <!-- Ready -->
    <p v-else class="mt-5 h-12 flex items-center justify-center gap-2 rounded-full bg-primary-soft text-primary text-[14px] font-medium">
      <AppIcon name="check" class="text-base pop-in" style="animation-delay: 80ms" />
      Ready for pickup
    </p>
  </article>
</template>
