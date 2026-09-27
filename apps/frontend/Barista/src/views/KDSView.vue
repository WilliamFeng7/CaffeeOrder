<script setup lang="ts">
/**
 * KDSView.vue
 * 
 * Premium Kitchen Display System Order Board.
 * Features: Three-column Kanban layout, stats bar, sound notifications, keyboard shortcuts.
 */
import AppIcon from '@shared/components/AppIcon.vue';
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import { useOrderPolling } from '../composables/useOrderPolling';
import { useKitchenDevice } from '../composables/useKitchenDevice';
import type { IconName } from '@shared/icons';
import OrderCard from '../components/OrderCard.vue';
import KDSLayout from '../components/KDSLayout.vue';

const toast = useToastStore();

// Global tick for OrderCard time updates (instead of per-card intervals)
const globalTick = ref(0);
let tickInterval: number | null = null;

// Screen stays awake, and the new-order beep works on the iPad (see the composable).
const { soundReady, beep } = useKitchenDevice();

// Polling is delegated to the shared composable. It replaces the ad-hoc 8s
// setInterval this view used to run, which (a) could overlap when a request was
// slower than the interval, (b) kept hammering the API while the KDS tab was
// hidden, and (c) duplicated the same fetch/new-order-diff logic that already
// existed, unused, in composables/useOrderPolling.ts.
const { orders, loading, refreshing, refresh } = useOrderPolling({
    interval: 8000,
    onNewOrders: (count) => {
        beep();
        toast.info(`${count} new order(s)!`);
    },
});

const handleStatusUpdate = async (orderId: number, status: string) => {
    // Staff call orders by pickup number, not by database id.
    const order = orders.value.find(o => o.id === orderId);
    const label = order?.pickup_number != null ? `#${order.pickup_number}` : `#${orderId}`;
    try {
        await api.updateOrderStatus(orderId, status);
        toast.success(`Order ${label} → ${status}`);
        await refresh();
    } catch (e) {
        toast.error('Failed to update status');
    }
};

// Backend statuses: created / processing / ready / completed / refunded
const pendingOrders = computed(() => orders.value.filter(o => o.status.toLowerCase() === 'created'));
const processingOrders = computed(() => orders.value.filter(o => o.status.toLowerCase() === 'processing'));
const completedOrders = computed(() => orders.value.filter(o => o.status.toLowerCase() === 'ready'));

// Stats
// The feed also carries older orders (finished ones, and any backlog left from
// previous days), so "today" is filtered on the order date. Counting the whole
// feed showed every order ever loaded, and averaging a months-old backlog into
// the wait time produced hundreds of thousands of minutes.
const isToday = (iso: string) => new Date(iso).toDateString() === new Date().toDateString();
const totalOrders = computed(() => orders.value.filter(o => isToday(o.created_at)).length);
const avgWaitTime = computed(() => {
  const activeTimes = [...pendingOrders.value, ...processingOrders.value]
    .filter(o => isToday(o.created_at))
    .map(o => Math.floor((Date.now() - new Date(o.created_at).getTime()) / 60000));
  if (activeTimes.length === 0) return null;
  return Math.round(activeTimes.reduce((a, b) => a + b, 0) / activeTimes.length);
});

// Keyboard shortcuts
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'r' && !e.ctrlKey && !e.metaKey) {
    refresh();
  }
};

// Polling lifecycle (start/stop, visibility pause, abort on unmount) is owned by
// useOrderPolling, which registers its own mounted/unmounted hooks.
onMounted(() => {
    // Global tick every 30s for OrderCard time updates
    tickInterval = setInterval(() => { globalTick.value++; }, 30000) as unknown as number;
    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    if (tickInterval) clearInterval(tickInterval);
    window.removeEventListener('keydown', handleKeydown);
});

const columns: { title: string; orders: typeof pendingOrders; icon: IconName; accentColor: string; iconBg: string; iconColor: string; countBg: string; borderColor: string }[] = [
  { 
    title: 'New Orders', 
    orders: pendingOrders, 
    icon: 'clock', 
    accentColor: 'amber',
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    countBg: 'bg-amber-500',
    borderColor: 'border-amber-100'
  },
  { 
    title: 'Making', 
    orders: processingOrders, 
    icon: 'flame', 
    accentColor: 'indigo',
    iconBg: 'bg-indigo-100',
    iconColor: 'text-indigo-600',
    countBg: 'bg-indigo-500',
    borderColor: 'border-indigo-100'
  },
  { 
    title: 'Ready', 
    orders: completedOrders, 
    icon: 'check-circle', 
    accentColor: 'emerald',
    iconBg: 'bg-emerald-100',
    iconColor: 'text-emerald-600',
    countBg: 'bg-emerald-500',
    borderColor: 'border-emerald-100'
  }
];

const manualRefresh = () => refresh();
</script>

<template>
  <KDSLayout :sound-ready="soundReady">
    <div class="flex flex-col h-full gap-3 md:gap-4">

      <!-- Stats + Refresh: one row instead of a hero title above a stats bar -->
      <div class="flex items-stretch gap-2 md:gap-3 animate-slide-up-content">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3 flex-1 min-w-0">
          <!-- Total Orders -->
          <div class="flex items-center gap-3 bg-white rounded-2xl px-3 py-2.5 shadow-sm border border-gray-50">
            <div class="size-9 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
              <AppIcon name="receipt" class="text-primary text-xl" />
            </div>
            <div class="min-w-0">
              <div class="text-xl font-black text-primary leading-none tabular-nums">{{ totalOrders }}</div>
              <div class="text-[10px] font-bold text-text-sub uppercase tracking-widest mt-1">Total Today</div>
            </div>
          </div>
          
          <!-- Active Orders -->
          <div class="flex items-center gap-3 bg-white rounded-2xl px-3 py-2.5 shadow-sm border border-gray-50">
            <div class="size-9 rounded-xl bg-amber-50 flex items-center justify-center shrink-0">
              <AppIcon name="hourglass" class="text-amber-500 text-xl" />
            </div>
            <div class="min-w-0">
              <div class="text-xl font-black text-primary leading-none tabular-nums">{{ pendingOrders.length + processingOrders.length }}</div>
              <div class="text-[10px] font-bold text-text-sub uppercase tracking-widest mt-1">Active</div>
            </div>
          </div>
          
          <!-- Average Wait -->
          <div class="flex items-center gap-3 bg-white rounded-2xl px-3 py-2.5 shadow-sm border border-gray-50">
            <div class="size-9 rounded-xl bg-secondary/30 flex items-center justify-center shrink-0">
              <AppIcon name="timer" class="text-secondary-content text-xl" />
            </div>
            <div class="min-w-0">
              <div class="text-xl font-black text-primary leading-none tabular-nums">
                <template v-if="avgWaitTime !== null">{{ avgWaitTime }}<span class="text-sm font-bold text-text-sub ml-0.5">min</span></template>
                <template v-else>—</template>
              </div>
              <div class="text-[10px] font-bold text-text-sub uppercase tracking-widest mt-1">Avg Wait</div>
            </div>
          </div>
          
          <!-- Ready Orders -->
          <div class="flex items-center gap-3 bg-white rounded-2xl px-3 py-2.5 shadow-sm border border-gray-50">
            <div class="size-9 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
              <AppIcon name="check-circle" weight="fill" class="text-emerald-500 text-xl" />
            </div>
            <div class="min-w-0">
              <div class="text-xl font-black text-primary leading-none tabular-nums">{{ completedOrders.length }}</div>
              <div class="text-[10px] font-bold text-text-sub uppercase tracking-widest mt-1">Ready</div>
            </div>
          </div>
        </div>

        <!-- Refresh Button (R on a keyboard does the same) -->
        <button 
          type="button"
          @click="manualRefresh"
          :disabled="refreshing"
          aria-label="Refresh"
          title="Refresh (R)"
          class="shrink-0 flex flex-col md:flex-row items-center justify-center gap-1 md:gap-2 px-4 md:px-5 bg-white rounded-2xl shadow-sm border border-gray-100 text-sm font-bold text-text-main hover:shadow-md disabled:opacity-50"
        >
          <AppIcon name="refresh" class="text-xl" :class="{ 'animate-spin': refreshing }" />
          <span class="hidden sm:inline">Refresh</span>
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="flex flex-col items-center gap-5 animate-fade-in">
          <div class="size-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
          <span class="text-text-sub font-bold text-sm">Loading orders...</span>
        </div>
      </div>

      <!-- KDS Three-Column Grid: side by side from iPad portrait up, so every
           status stays in view (stacked, only one order card fitted on screen) -->
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 flex-1 min-h-0">
        <div 
          v-for="(col, idx) in columns" 
          :key="col.title" 
          class="flex flex-col h-full min-h-[320px] md:min-h-0 min-w-0 bg-white rounded-[24px] md:rounded-[28px] p-3 lg:p-4 border shadow-sm animate-slide-up-content"
          :class="col.borderColor"
          :style="{ animationDelay: `${40 + idx * 40}ms` }"
        >
          <!-- Column Header -->
          <div class="flex items-center justify-between gap-3 mb-3 pb-3 border-b border-gray-100/80">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="size-9 lg:size-10 rounded-xl flex items-center justify-center shrink-0" :class="col.iconBg">
                <AppIcon :name="col.icon" weight="fill" class="text-xl" :class="col.iconColor" />
              </div>
              <h2 class="text-base lg:text-lg font-black tracking-tight text-primary truncate">{{ col.title }}</h2>
            </div>
            <span 
              class="min-w-8 h-8 px-2 rounded-xl flex items-center justify-center text-sm font-black text-white shadow-lg tabular-nums" 
              :class="col.countBg"
            >
              {{ col.orders.value.length }}
            </span>
          </div>

          <!-- Scrollable Order List (TransitionGroup uses the .list-* styles below) -->
          <TransitionGroup tag="div" name="list" class="flex-1 overflow-y-auto pr-1 space-y-3 no-scrollbar scroll-smooth-touch relative">
            <OrderCard
              v-for="order in col.orders.value"
              :key="order.id"
              :order="order"
              :global-tick="globalTick"
              @update-status="handleStatusUpdate"
            />

            <!-- Empty State -->
            <div v-if="col.orders.value.length === 0" key="empty" class="h-40 md:h-48 flex flex-col items-center justify-center text-gray-400 animate-fade-in">
              <div class="size-20 rounded-[24px] bg-gray-50 flex items-center justify-center mb-3 shadow-inner">
                <AppIcon name="coffee" class="text-4xl opacity-40" />
              </div>
              <span class="text-xs font-bold uppercase tracking-widest">No orders</span>
            </div>
          </TransitionGroup>
        </div>
      </div>
    </div>
  </KDSLayout>
</template>

<style scoped>
/* Cards glide into their new column and settle; leaving is quicker. */
.list-move,
.list-enter-active {
  transition: transform var(--dur-enter) var(--ease-out), opacity var(--dur-fade) var(--ease-out);
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: scale(0.97) translateY(12px);
}
.list-leave-active {
  transition: transform var(--dur-sheet-out) var(--ease-out), opacity var(--dur-sheet-out) var(--ease-out);
  position: absolute;
  width: calc(100% - 0.25rem);
}
</style>
