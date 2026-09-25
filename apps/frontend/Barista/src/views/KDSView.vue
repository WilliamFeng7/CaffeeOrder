<script setup lang="ts">
/**
 * KDSView.vue
 * 
 * Premium Kitchen Display System Order Board.
 * Features: Three-column Kanban layout, stats bar, sound notifications, keyboard shortcuts.
 */
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import { useOrderPolling } from '../composables/useOrderPolling';
import OrderCard from '../components/OrderCard.vue';
import KDSLayout from '../components/KDSLayout.vue';

const toast = useToastStore();

// Global tick for OrderCard time updates (instead of per-card intervals)
const globalTick = ref(0);
let tickInterval: number | null = null;

// Sound notification
const playNotificationSound = () => {
  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.3);
  } catch (e) {
    // Audio not supported
  }
};

// Polling is delegated to the shared composable. It replaces the ad-hoc 8s
// setInterval this view used to run, which (a) could overlap when a request was
// slower than the interval, (b) kept hammering the API while the KDS tab was
// hidden, and (c) duplicated the same fetch/new-order-diff logic that already
// existed, unused, in composables/useOrderPolling.ts.
const { orders, loading, refreshing, refresh } = useOrderPolling({
    interval: 8000,
    onNewOrders: (count) => {
        playNotificationSound();
        toast.info(`${count} new order(s)!`);
    },
});

const handleStatusUpdate = async (orderId: number, status: string) => {
    try {
        await api.updateOrderStatus(orderId, status);
        toast.success(`Order #${orderId} → ${status}`);
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
const totalOrders = computed(() => orders.value.length);
const avgWaitTime = computed(() => {
  const activeTimes = [...pendingOrders.value, ...processingOrders.value].map(o => 
    Math.floor((Date.now() - new Date(o.created_at).getTime()) / 60000)
  );
  if (activeTimes.length === 0) return 0;
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

const columns = [
  { 
    title: 'New Orders', 
    orders: pendingOrders, 
    icon: 'schedule', 
    accentColor: 'amber',
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    countBg: 'bg-amber-500',
    borderColor: 'border-amber-100'
  },
  { 
    title: 'Making', 
    orders: processingOrders, 
    icon: 'local_fire_department', 
    accentColor: 'indigo',
    iconBg: 'bg-indigo-100',
    iconColor: 'text-indigo-600',
    countBg: 'bg-indigo-500',
    borderColor: 'border-indigo-100'
  },
  { 
    title: 'Ready', 
    orders: completedOrders, 
    icon: 'check_circle', 
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
  <KDSLayout>
    <div class="flex flex-col h-full gap-5 md:gap-6">
      
      <!-- Hero Section -->
      <div class="flex flex-wrap items-end justify-between gap-4 px-1">
        <div class="animate-slide-up-content">
          <h1 class="text-4xl md:text-5xl lg:text-6xl font-sans font-black text-primary leading-[0.95] tracking-tighter">
            Order Board
          </h1>
          <p class="text-sm md:text-base font-serif italic text-text-sub ml-0.5 mt-2 flex items-center gap-2">
            <span>Real-time order management</span>
            <kbd class="px-2 py-1 bg-white rounded-lg text-[10px] font-mono font-bold not-italic text-gray-400 border border-gray-100 shadow-sm">R</kbd>
            <span class="text-gray-300">to refresh</span>
          </p>
        </div>
        
        <!-- Refresh Button -->
        <button 
          @click="manualRefresh"
          :disabled="refreshing"
          class="flex items-center gap-2.5 px-5 py-3 bg-white rounded-2xl shadow-sm border border-gray-100 text-sm font-bold text-text-main hover:shadow-md active:scale-95 transition-all duration-300 disabled:opacity-50 animate-slide-up-content"
          style="animation-delay: 100ms"
        >
          <span class="material-symbols-rounded text-xl" :class="{ 'animate-spin': refreshing }">refresh</span>
          <span class="hidden sm:inline">Refresh</span>
        </button>
      </div>

      <!-- Quick Stats Bar -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 animate-slide-up-content" style="animation-delay: 150ms">
        <!-- Total Orders -->
        <div class="flex items-center gap-3 bg-white rounded-2xl px-4 py-3.5 shadow-sm border border-gray-50">
          <div class="size-11 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-primary text-xl">receipt_long</span>
          </div>
          <div class="min-w-0">
            <div class="text-2xl font-black text-primary leading-none">{{ totalOrders }}</div>
            <div class="text-[10px] font-bold text-text-sub uppercase tracking-widest mt-0.5">Total Today</div>
          </div>
        </div>
        
        <!-- Active Orders -->
        <div class="flex items-center gap-3 bg-white rounded-2xl px-4 py-3.5 shadow-sm border border-gray-50">
          <div class="size-11 rounded-xl bg-amber-50 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-amber-500 text-xl">pending</span>
          </div>
          <div class="min-w-0">
            <div class="text-2xl font-black text-primary leading-none">{{ pendingOrders.length + processingOrders.length }}</div>
            <div class="text-[10px] font-bold text-text-sub uppercase tracking-widest mt-0.5">Active</div>
          </div>
        </div>
        
        <!-- Average Wait -->
        <div class="flex items-center gap-3 bg-white rounded-2xl px-4 py-3.5 shadow-sm border border-gray-50">
          <div class="size-11 rounded-xl bg-secondary/30 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-secondary-content text-xl">timer</span>
          </div>
          <div class="min-w-0">
            <div class="text-2xl font-black text-primary leading-none">{{ avgWaitTime }}<span class="text-sm font-bold text-text-sub ml-0.5">min</span></div>
            <div class="text-[10px] font-bold text-text-sub uppercase tracking-widest mt-0.5">Avg Wait</div>
          </div>
        </div>
        
        <!-- Ready Orders -->
        <div class="flex items-center gap-3 bg-white rounded-2xl px-4 py-3.5 shadow-sm border border-gray-50">
          <div class="size-11 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-emerald-500 text-xl filled">check_circle</span>
          </div>
          <div class="min-w-0">
            <div class="text-2xl font-black text-primary leading-none">{{ completedOrders.length }}</div>
            <div class="text-[10px] font-bold text-text-sub uppercase tracking-widest mt-0.5">Ready</div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="flex flex-col items-center gap-5 animate-fade-in">
          <div class="size-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
          <span class="text-text-sub font-bold text-sm">Loading orders...</span>
        </div>
      </div>

      <!-- KDS Three-Column Grid -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-5 flex-1 min-h-0 pb-4">
        <div 
          v-for="(col, idx) in columns" 
          :key="col.title" 
          class="flex flex-col h-full min-h-[320px] lg:min-h-0 bg-white rounded-[28px] md:rounded-[32px] p-4 md:p-5 border shadow-sm transition-all duration-500 ease-luxury hover:shadow-md animate-slide-up-content"
          :class="col.borderColor"
          :style="{ animationDelay: `${200 + idx * 80}ms` }"
        >
          <!-- Column Header -->
          <div class="flex items-center justify-between gap-3 mb-4 pb-4 border-b border-gray-100/80">
            <div class="flex items-center gap-3">
              <div class="size-10 md:size-11 rounded-xl flex items-center justify-center" :class="col.iconBg">
                <span class="material-symbols-rounded text-xl md:text-2xl filled" :class="col.iconColor">{{ col.icon }}</span>
              </div>
              <h2 class="text-lg md:text-xl font-black tracking-tight text-primary">{{ col.title }}</h2>
            </div>
            <span 
              class="size-8 md:size-9 rounded-xl flex items-center justify-center text-sm font-black text-white shadow-lg" 
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
            <div v-if="col.orders.value.length === 0" key="empty" class="h-40 md:h-48 flex flex-col items-center justify-center text-gray-300 animate-fade-in">
              <div class="size-20 md:size-24 rounded-[24px] bg-gray-50 flex items-center justify-center mb-3 shadow-inner">
                <span class="material-symbols-rounded text-4xl md:text-5xl opacity-30">coffee</span>
              </div>
              <span class="text-xs font-bold uppercase tracking-widest opacity-50">No orders</span>
            </div>
          </TransitionGroup>
        </div>
      </div>
    </div>
  </KDSLayout>
</template>

<style scoped>
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(10px);
}
.list-leave-active {
  position: absolute;
  width: calc(100% - 0.25rem);
}
</style>
