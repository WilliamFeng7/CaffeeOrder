<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { api, type Order } from '../api';
import { useToastStore } from '../stores/toast';
import OrderCard from '../components/OrderCard.vue';
import KDSLayout from '../components/KDSLayout.vue';

const orders = ref<Order[]>([]);
const loading = ref(true);
const toast = useToastStore();
let pollInterval: number | null = null;

const fetchOrders = async () => {
    try {
        const data = await api.getAllOrders();
        orders.value = data.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    } catch (e) {
        console.error("Failed to fetch orders", e);
    } finally {
        loading.value = false;
    }
};

const handleStatusUpdate = async (orderId: number, status: string) => {
    try {
        await api.updateOrderStatus(orderId, status);
        toast.success(`Order #${orderId} marked as ${status}`);
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

onMounted(() => {
    fetchOrders();
    pollInterval = setInterval(fetchOrders, 4000) as unknown as number;
});

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval);
});

const columns = [
  { title: 'New Orders', orders: pendingOrders, icon: 'schedule', bgColor: 'bg-amber-50', iconColor: 'text-amber-500', countBg: 'bg-amber-500' },
  { title: 'In Progress', orders: processingOrders, icon: 'local_fire_department', bgColor: 'bg-indigo-50', iconColor: 'text-indigo-500', countBg: 'bg-indigo-500' },
  { title: 'Ready', orders: completedOrders, icon: 'check_circle', bgColor: 'bg-emerald-50', iconColor: 'text-emerald-500', countBg: 'bg-emerald-500' }
];
</script>

<template>
  <KDSLayout>
    <div class="flex flex-col h-full gap-4 md:gap-6 pb-8">
      <!-- Hero Section -->
      <div class="px-1 md:px-2">
        <div class="relative overflow-hidden pb-1">
          <h1 class="text-4xl md:text-6xl lg:text-7xl font-sans font-black text-primary leading-[0.9] tracking-tighter animate-text-reveal transform-gpu">
            Order Board
          </h1>
        </div>
        <p class="text-base md:text-lg font-serif italic text-text-sub ml-0.5 opacity-80 animate-slide-up-content" style="animation-delay: 200ms">
          Current active orders
        </p>
      </div>

      <!-- Quick Stats Bar -->
      <div class="flex flex-wrap gap-3 md:gap-4 animate-slide-up-content" style="animation-delay: 300ms">
        <div class="flex items-center gap-3 bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-100">
          <div class="size-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <span class="material-symbols-rounded text-primary text-xl">receipt_long</span>
          </div>
          <div>
            <div class="text-2xl font-black text-primary leading-none">{{ totalOrders }}</div>
            <div class="text-[10px] font-bold text-text-sub uppercase tracking-wide">Total Orders</div>
          </div>
        </div>
        
        <div class="flex items-center gap-3 bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-100">
          <div class="size-10 rounded-xl bg-amber-50 flex items-center justify-center">
            <span class="material-symbols-rounded text-amber-500 text-xl">pending</span>
          </div>
          <div>
            <div class="text-2xl font-black text-primary leading-none">{{ pendingOrders.length + processingOrders.length }}</div>
            <div class="text-[10px] font-bold text-text-sub uppercase tracking-wide">Active</div>
          </div>
        </div>
        
        <div class="flex items-center gap-3 bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-100">
          <div class="size-10 rounded-xl bg-secondary/30 flex items-center justify-center">
            <span class="material-symbols-rounded text-secondary-content text-xl">timer</span>
          </div>
          <div>
            <div class="text-2xl font-black text-primary leading-none">{{ avgWaitTime }}<span class="text-sm font-bold text-text-sub ml-0.5">m</span></div>
            <div class="text-[10px] font-bold text-text-sub uppercase tracking-wide">Avg Wait</div>
          </div>
        </div>
        
        <div class="flex items-center gap-3 bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-100">
          <div class="size-10 rounded-xl bg-emerald-50 flex items-center justify-center">
            <span class="material-symbols-rounded text-emerald-500 text-xl filled">check_circle</span>
          </div>
          <div>
            <div class="text-2xl font-black text-primary leading-none">{{ completedOrders.length }}</div>
            <div class="text-[10px] font-bold text-text-sub uppercase tracking-wide">Ready</div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="flex flex-col items-center gap-4 animate-fade-in">
          <div class="size-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
          <span class="text-text-sub font-bold">Loading orders...</span>
        </div>
      </div>

      <!-- KDS Grid -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-5 flex-1 min-h-0">
        <div 
          v-for="(col, idx) in columns" 
          :key="col.title" 
          class="flex flex-col h-full min-h-[300px] lg:min-h-0 bg-white rounded-[28px] md:rounded-[36px] p-4 md:p-5 border border-gray-100 shadow-sm transition-all duration-500 ease-luxury hover:shadow-md animate-slide-up-content transform-gpu"
          :style="{ animationDelay: `${400 + idx * 80}ms` }"
        >
          <!-- Header -->
          <div class="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-gray-100">
            <div class="flex items-center gap-2.5">
              <div class="size-9 md:size-10 rounded-xl flex items-center justify-center" :class="col.bgColor">
                <span class="material-symbols-rounded text-xl md:text-2xl" :class="col.iconColor">{{ col.icon }}</span>
              </div>
              <h2 class="text-lg md:text-xl font-black tracking-tight text-primary">{{ col.title }}</h2>
            </div>
            <span class="size-7 md:size-8 rounded-full flex items-center justify-center text-xs md:text-sm font-black text-white shadow-md" :class="col.countBg">
              {{ col.orders.value.length }}
            </span>
          </div>

          <!-- Scrollable List -->
          <div class="flex-1 overflow-y-auto pr-1 space-y-3 md:space-y-4 no-scrollbar scroll-smooth-touch">
            <TransitionGroup name="list">
              <OrderCard 
                v-for="(order, i) in col.orders.value" 
                :key="order.id" 
                :order="order" 
                @update-status="handleStatusUpdate"
                class="animate-slide-up-content"
                :style="{ animationDelay: `${(idx * 80) + (i * 40)}ms` }"
              />
            </TransitionGroup>

            <!-- Empty State -->
            <div v-if="col.orders.value.length === 0" class="h-40 md:h-48 flex flex-col items-center justify-center text-gray-300 animate-fade-in">
              <div class="size-16 md:size-20 rounded-full bg-gray-50 flex items-center justify-center mb-3 shadow-inner">
                <span class="material-symbols-rounded text-3xl md:text-4xl opacity-25">coffee</span>
              </div>
              <span class="text-[10px] font-black uppercase tracking-[0.15em] opacity-50">No orders here</span>
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
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
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
