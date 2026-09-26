<script setup lang="ts">
/**
 * OrderCard.vue
 * 
 * Premium order card for KDS display.
 * Features: Elegant styling, time tracking, item pills, action buttons.
 */
import type { Order } from '../api';
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  order: Order;
  globalTick?: number; // Parent provides this to trigger time recalculation
}>();

const emit = defineEmits<{
  (e: 'update-status', orderId: number, status: string): void;
}>();

// Time elapsed - now computed, triggered by globalTick from parent
// This eliminates the need for per-card setInterval (O(n) -> O(1) timers)
const timeElapsed = computed(() => {
  // Access globalTick to trigger reactivity on parent's interval
  const _ = props.globalTick;
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

const waitMinutes = computed(() => Math.floor((Date.now() - new Date(props.order.created_at).getTime()) / 60000));

const isUrgent = computed(() => {
  // Backend statuses: created / processing / ready / completed / refunded
  if (['ready', 'completed', 'refunded'].includes(props.order.status.toLowerCase())) return false;
  return waitMinutes.value > 10;
});

const nextAction = computed(() => {
  const s = props.order.status.toLowerCase();
  if (s === 'created') return {
    label: 'Start Making',
    action: 'processing',
    icon: 'play_arrow',
    bgClass: 'bg-primary hover:bg-primary/90',
    textClass: 'text-white'
  };
  if (s === 'processing') return {
    label: 'Mark Ready',
    action: 'ready',
    icon: 'check',
    bgClass: 'bg-secondary hover:bg-secondary/90',
    textClass: 'text-secondary-content'
  };
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
  <div 
    class="bg-white p-3 md:p-4 rounded-[20px] relative overflow-hidden border border-gray-100/80 shadow-sm"
    :class="{ 'ring-2 ring-red-400/60 border-red-200 bg-red-50/30': isUrgent }"
  >
    <!-- Order Header -->
    <div class="flex items-center justify-between gap-3 mb-3 relative z-10">
      <div class="flex items-center gap-3 min-w-0">
        <!-- Pickup Number Badge: the number the customer holds -->
        <div class="min-w-12 h-12 px-2 rounded-xl bg-gradient-to-br from-primary to-[#0A2921] text-white flex items-center justify-center font-black text-lg shadow-lg shadow-primary/20 tabular-nums shrink-0" :title="`Order ${order.id}`">
          #{{ order.pickup_number ?? order.id }}
        </div>
        <div class="flex flex-col min-w-0">
          <span class="text-sm font-bold text-text-main tabular-nums">{{ formatTime(order.created_at) }}</span>
          <span class="text-xs font-bold flex items-center gap-1.5" :class="isUrgent ? 'text-red-600' : 'text-text-sub'">
            <span class="material-symbols-rounded text-sm" :class="isUrgent ? 'filled' : ''" aria-hidden="true">{{ isUrgent ? 'warning' : 'schedule' }}</span>
            {{ timeElapsed }} ago
          </span>
        </div>
      </div>
      
      <!-- Item Count & Urgent Badge -->
      <div class="flex items-center gap-2 shrink-0">
        <span class="text-[11px] font-bold text-text-sub bg-gray-100 px-2.5 py-1 rounded-lg">{{ itemCount }} {{ itemCount === 1 ? 'item' : 'items' }}</span>
        <div v-if="isUrgent" class="size-8 rounded-lg bg-red-500 flex items-center justify-center shadow-lg shadow-red-500/30" aria-label="Waiting over 10 minutes">
          <span class="material-symbols-rounded text-white text-base filled" aria-hidden="true">priority_high</span>
        </div>
      </div>
    </div>

    <!-- Items List -->
    <div class="space-y-2 mb-3 relative z-10">
      <div 
        v-for="(item, i) in order.items" 
        :key="i" 
        class="flex items-center gap-2.5 py-2 px-3 bg-background-light rounded-xl border border-gray-50"
      >
        <!-- Quantity Badge -->
        <span class="size-7 rounded-lg bg-primary text-white text-xs font-black flex items-center justify-center shrink-0 shadow-sm">
          {{ item.quantity }}×
        </span>
        
        <!-- Item Name -->
        <span class="text-sm font-bold text-text-main flex-1 truncate">{{ item.name }}</span>
        
        <!-- Options Chips -->
        <div class="flex items-center gap-1.5 shrink-0">
          <span 
            v-if="item.temperature" 
            class="text-[10px] font-bold px-2 py-1 rounded-lg flex items-center gap-1" 
            :class="item.temperature === 'Hot' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'"
          >
            <span class="material-symbols-rounded text-xs" aria-hidden="true">{{ item.temperature === 'Hot' ? 'local_fire_department' : 'ac_unit' }}</span>
            {{ item.temperature }}
          </span>
          <span 
            v-if="item.sugar" 
            class="text-[10px] font-bold px-2 py-1 rounded-lg bg-amber-100 text-amber-700"
          >
            {{ item.sugar }}
          </span>
        </div>
      </div>
    </div>

    <!-- Action Button -->
    <button 
      v-if="nextAction"
      type="button"
      @click="runAction"
      :disabled="pending"
      class="w-full py-3 rounded-xl text-sm font-black shadow-lg disabled:opacity-60 flex items-center justify-center gap-2 relative z-10"
      :class="[nextAction.bgClass, nextAction.textClass]"
    >
      <span v-if="pending" class="size-4 border-2 border-current border-r-transparent rounded-full animate-spin" aria-hidden="true"></span>
      <span v-else class="material-symbols-rounded text-xl" aria-hidden="true">{{ nextAction.icon }}</span>
      <span>{{ nextAction.label }}</span>
    </button>
    
    <!-- Completed State -->
    <div 
      v-else 
      class="w-full py-3 rounded-xl bg-emerald-100 text-emerald-700 text-sm font-bold text-center flex items-center justify-center gap-2 relative z-10"
    >
      <span class="material-symbols-rounded text-xl filled" aria-hidden="true">check_circle</span>
      <span>Ready for Pickup</span>
    </div>
  </div>
</template>
