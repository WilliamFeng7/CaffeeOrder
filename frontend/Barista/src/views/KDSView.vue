<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { api, type Order } from '../api';
import { useToastStore } from '../stores/toast';
import OrderCard from '../components/OrderCard.vue';
import KDSLayout from '../components/KDSLayout.vue';

const orders = ref<Order[]>([]);
const loading = ref(true);
const refreshing = ref(false);
const toast = useToastStore();
let pollInterval: number | null = null;

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

const previousPendingCount = ref(0);

const fetchOrders = async (showRefresh = false) => {
    if (showRefresh) refreshing.value = true;
    try {
        const data = await api.getAllOrders();
        const newOrders = data.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        
        // Check for new pending orders
        const newPendingCount = newOrders.filter(o => ['pending', 'new'].includes(o.status.toLowerCase())).length;
        if (previousPendingCount.value > 0 && newPendingCount > previousPendingCount.value) {
          playNotificationSound();
          toast.info(`${newPendingCount - previousPendingCount.value} new order(s)!`);
        }
        previousPendingCount.value = newPendingCount;
        
        orders.value = newOrders;
    } catch (e) {
        console.error("Failed to fetch orders", e);
    } finally {
        loading.value = false;
        refreshing.value = false;
    }
};

const handleStatusUpdate = async (orderId: number, status: string) => {
    try {
        await api.updateOrderStatus(orderId, status);
        toast.success(`Order #${orderId} → ${status}`);
        await fetchOrders();
    } catch (e) {
        toast.error('Failed to update status');
    }
};

const pendingOrders = computed(() => orders.value.filter(o => ['pending', 'new'].includes(o.status.toLowerCase())));
const processingOrders = computed(() => orders.value.filter(o => ['processing', 'inprogress'].includes(o.status.toLowerCase())));
const completedOrders = computed(() => orders.value.filter(o => ['completed', 'done'].includes(o.status.toLowerCase())));

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
    fetchOrders(true);
  }
};

onMounted(() => {
    fetchOrders();
    pollInterval = setInterval(() => fetchOrders(), 4000) as unknown as number;
    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval);
    window.removeEventListener('keydown', handleKeydown);
});

const columns = [
  { title: 'New', orders: pendingOrders, icon: 'schedule', bgColor: 'bg-amber-50', iconColor: 'text-amber-500', countBg: 'bg-amber-500', borderColor: 'border-amber-200' },
  { title: 'Making', orders: processingOrders, icon: 'local_fire_department', bgColor: 'bg-indigo-50', iconColor: 'text-indigo-500', countBg: 'bg-indigo-500', borderColor: 'border-indigo-200' },
  { title: 'Ready', orders: completedOrders, icon: 'check_circle', bgColor: 'bg-emerald-50', iconColor: 'text-emerald-500', countBg: 'bg-emerald-500', borderColor: 'border-emerald-200' }
];

const manualRefresh = () => fetchOrders(true);
</script>

<template>
  <KDSLayout>
    <div class="flex flex-col h-full gap-4 md:gap-5 pb-8">
      <!-- Hero Section -->
      <div class="flex flex-wrap items-end justify-between gap-4 px-1 md:px-2">
        <div>
          <h1 class="text-4xl md:text-5xl lg:text-6xl font-sans font-black text-primary leading-[0.9] tracking-tighter animate-text-reveal transform-gpu">
            Order Board
          </h1>
          <p class="text-sm md:text-base font-serif italic text-text-sub ml-0.5 opacity-80 mt-1">
            Current active orders · Press <kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-[10px] font-mono font-bold not-italic">R</kbd> to refresh
          </p>
        </div>
        
        <!-- Refresh Button -->
        <button 
          @click="manualRefresh"
          :disabled="refreshing"
          class="flex items-center gap-2 px-4 py-2.5 bg-white rounded-xl shadow-sm border border-gray-100 text-sm font-bold text-text-main hover:shadow-md active:scale-95 transition-all disabled:opacity-50"
        >
          <span class="material-symbols-rounded text-lg" :class="{ 'animate-spin': refreshing }">refresh</span>
          <span class="hidden sm:inline">Refresh</span>
        </button>
      </div>

      <!-- Quick Stats Bar -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3 animate-slide-up-content" style="animation-delay: 200ms">
        <div class="flex items-center gap-2.5 bg-white rounded-xl px-3 py-2.5 shadow-sm border border-gray-100">
          <div class="size-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-primary text-lg">receipt_long</span>
          </div>
          <div class="min-w-0">
            <div class="text-xl font-black text-primary leading-none">{{ totalOrders }}</div>
            <div class="text-[9px] font-bold text-text-sub uppercase tracking-wide truncate">Total</div>
          </div>
        </div>
        
        <div class="flex items-center gap-2.5 bg-white rounded-xl px-3 py-2.5 shadow-sm border border-gray-100">
          <div class="size-8 rounded-lg bg-amber-50 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-amber-500 text-lg">pending</span>
          </div>
          <div class="min-w-0">
            <div class="text-xl font-black text-primary leading-none">{{ pendingOrders.length + processingOrders.length }}</div>
            <div class="text-[9px] font-bold text-text-sub uppercase tracking-wide truncate">Active</div>
          </div>
        </div>
        
        <div class="flex items-center gap-2.5 bg-white rounded-xl px-3 py-2.5 shadow-sm border border-gray-100">
          <div class="size-8 rounded-lg bg-secondary/30 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-secondary-content text-lg">timer</span>
          </div>
          <div class="min-w-0">
            <div class="text-xl font-black text-primary leading-none">{{ avgWaitTime }}<span class="text-xs font-bold text-text-sub">m</span></div>
            <div class="text-[9px] font-bold text-text-sub uppercase tracking-wide truncate">Avg Wait</div>
          </div>
        </div>
        
        <div class="flex items-center gap-2.5 bg-white rounded-xl px-3 py-2.5 shadow-sm border border-gray-100">
          <div class="size-8 rounded-lg bg-emerald-50 flex items-center justify-center shrink-0">
            <span class="material-symbols-rounded text-emerald-500 text-lg filled">check_circle</span>
          </div>
          <div class="min-w-0">
            <div class="text-xl font-black text-primary leading-none">{{ completedOrders.length }}</div>
            <div class="text-[9px] font-bold text-text-sub uppercase tracking-wide truncate">Ready</div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="flex flex-col items-center gap-4 animate-fade-in">
          <div class="size-14 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
          <span class="text-text-sub font-bold text-sm">Loading orders...</span>
        </div>
      </div>

      <!-- KDS Grid -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-3 md:gap-4 flex-1 min-h-0">
        <div 
          v-for="(col, idx) in columns" 
          :key="col.title" 
          class="flex flex-col h-full min-h-[280px] lg:min-h-0 bg-white rounded-[24px] md:rounded-[28px] p-3 md:p-4 border shadow-sm transition-all duration-500 ease-luxury hover:shadow-md animate-slide-up-content transform-gpu"
          :class="col.borderColor"
          :style="{ animationDelay: `${300 + idx * 60}ms` }"
        >
          <!-- Header -->
          <div class="flex items-center justify-between gap-2 mb-3 pb-2.5 border-b border-gray-100">
            <div class="flex items-center gap-2">
              <div class="size-8 rounded-lg flex items-center justify-center" :class="col.bgColor">
                <span class="material-symbols-rounded text-lg" :class="col.iconColor">{{ col.icon }}</span>
              </div>
              <h2 class="text-base md:text-lg font-black tracking-tight text-primary">{{ col.title }}</h2>
            </div>
            <span class="size-6 md:size-7 rounded-full flex items-center justify-center text-xs font-black text-white shadow" :class="col.countBg">
              {{ col.orders.value.length }}
            </span>
          </div>

          <!-- Scrollable List -->
          <div class="flex-1 overflow-y-auto pr-0.5 space-y-2.5 md:space-y-3 no-scrollbar scroll-smooth-touch">
            <TransitionGroup name="list">
              <OrderCard 
                v-for="order in col.orders.value" 
                :key="order.id" 
                :order="order" 
                @update-status="handleStatusUpdate"
              />
            </TransitionGroup>

            <!-- Empty State -->
            <div v-if="col.orders.value.length === 0" class="h-32 md:h-40 flex flex-col items-center justify-center text-gray-300 animate-fade-in">
              <div class="size-14 md:size-16 rounded-full bg-gray-50 flex items-center justify-center mb-2 shadow-inner">
                <span class="material-symbols-rounded text-2xl md:text-3xl opacity-20">coffee</span>
              </div>
              <span class="text-[9px] font-bold uppercase tracking-[0.1em] opacity-40">Empty</span>
            </div>
          </div>
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
  transform: scale(0.96) translateY(8px);
}
.list-leave-active {
  position: absolute;
  width: calc(100% - 0.125rem);
}
</style>
