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
        // Sort by Created Date
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

onMounted(() => {
    fetchOrders();
    pollInterval = setInterval(fetchOrders, 4000) as unknown as number;
});

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval);
});

const columns = [
  { title: 'New Orders', orders: pendingOrders, color: 'text-text-main', countColor: 'bg-primary text-white' },
  { title: 'In Progress', orders: processingOrders, color: 'text-text-main', countColor: 'bg-secondary text-primary-content' },
  { title: 'Ready for Pickup', orders: completedOrders, color: 'text-text-main', countColor: 'bg-green-100 text-green-700' }
];
</script>

<template>
  <KDSLayout>
    <div class="flex flex-col h-full">
      <!-- Hero Section (Matches Student HomeView "Good Morning") -->
      <div class="mb-8 px-2 animate-slide-down-content">
          <h1 class="text-6xl md:text-8xl font-sans font-black text-[#103E32] leading-[0.9] tracking-tighter mb-2">
            Order Board
          </h1>
          <p class="text-xl font-serif italic text-text-sub ml-2 opacity-80">
            Current active orders
          </p>
      </div>

      <!-- KDS Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1 min-h-0 pb-20">
        <div 
          v-for="(col, idx) in columns" 
          :key="col.title" 
          class="flex flex-col h-full min-h-0 bg-white/40 rounded-[40px] p-4 border border-white/50 backdrop-blur-sm shadow-sm transition-all hover:bg-white/60 hover:shadow-md"
        >
           <!-- Header -->
           <div class="flex items-center justify-between gap-3 mb-6 px-4 pt-2 animate-slide-up-content" :style="{ animationDelay: `${idx * 100}ms` }">
               <h2 class="text-3xl font-black tracking-tight text-[#103E32]">{{ col.title }}</h2>
               <span class="size-10 rounded-full flex items-center justify-center text-sm font-black shadow-inner" :class="col.countColor">
                  {{ col.orders.value.length }}
               </span>
           </div>

           <!-- Scrollable List -->
           <div class="flex-1 overflow-y-auto pr-2 space-y-5 no-scrollbar px-1">
               <TransitionGroup name="list">
                  <OrderCard 
                      v-for="(order, i) in col.orders.value" 
                      :key="order.id" 
                      :order="order" 
                      @update-status="handleStatusUpdate"
                      class="animate-slide-up-content"
                      :style="{ animationDelay: `${(idx * 100) + (i * 50)}ms` }"
                  />
               </TransitionGroup>

               <!-- Empty State (Beautiful Illustration Style) -->
               <div v-if="col.orders.value.length === 0" class="h-64 flex flex-col items-center justify-center text-gray-300 animate-fade-in">
                   <div class="size-24 rounded-full bg-gray-50 flex items-center justify-center mb-4 shadow-inner">
                       <span class="material-symbols-rounded text-5xl opacity-20">coffee</span>
                   </div>
                   <span class="text-xs font-black uppercase tracking-[0.2em] opacity-60">No orders here</span>
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
  transform: scale(0.95);
}
.list-leave-active {
  position: absolute;
  width: 100%;
}
</style>
