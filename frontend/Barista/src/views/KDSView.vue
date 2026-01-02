
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { api, type Order } from '../api';
import { useToastStore } from '../stores/toast';

const orders = ref<Order[]>([]);
const loading = ref(true);
const filter = ref<'pending' | 'all'>('pending');
const router = useRouter();
const toast = useToastStore();
let pollInterval: any = null;

const fetchOrders = async () => {
    try {
        const allOrders = await api.getAllOrders();
        orders.value = allOrders;
        loading.value = false;
    } catch (e: any) {
        console.error("Polling error", e);
        if (e.response && e.response.status === 401) {
            toast.error('Session expired. Please login again.');
            router.push('/login');
        }
    }
};

const completeOrder = async (orderId: number) => {
    try {
        await api.updateOrderStatus(orderId, 'completed');
        toast.success(`Order #${orderId} Completed!`);
        // Optimistic update if viewing pending
        if (filter.value === 'pending') {
             orders.value = orders.value.filter(o => o.id !== orderId);
        }
        await fetchOrders(); // Sync
    } catch (e: any) {
        toast.error('Failed to complete order: ' + e.message);
    }
};

onMounted(() => {
    fetchOrders();
    // Poll every 2 seconds
    pollInterval = setInterval(fetchOrders, 2000);
});

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval);
});

// Computed properties for filtering
const filteredOrders = computed(() => {
    if (filter.value === 'all') return orders.value;
    // KDS 'Pending' means Created (Paid) or Processing. 
    return orders.value.filter(o => ['created', 'processing'].includes(o.status));
});


// Helper for Spec Parsing (frontend sees spec as object)
const parseSpecs = (item: any) => {
    if (!item.spec) return [];
    if (typeof item.spec === 'string') {
        try {
            return Object.entries(JSON.parse(item.spec));
        } catch {
            return [];
        }
    }
    return Object.entries(item.spec);
};

// UI Helpers
const getStatusColor = (status: string) => {
    if (status === 'created') return 'bg-yellow-50 text-yellow-700 border-yellow-200';
    if (status === 'processing') return 'bg-blue-50 text-blue-700 border-blue-200';
    if (status === 'completed') return 'bg-green-50 text-green-700 border-green-200';
    return 'bg-gray-50 text-gray-700';
};
</script>

<template>
    <div class="min-h-screen p-4 md:p-6 pb-20 animate-fade-in bg-background-light">
        <!-- Header -->
        <header class="flex justify-between items-center mb-6 sticky top-0 bg-background-light/95 backdrop-blur z-20 py-2">
            <div>
                <h1 class="text-3xl font-black text-primary font-serif italic tracking-tight">KDS Display</h1>
                <p class="text-sm text-gray-400 font-bold tracking-wide">Kitchen Management System</p>
            </div>
            
            <div class="flex items-center gap-4">
                 <!-- Filter Toggle -->
                <div class="bg-white p-1 rounded-xl border border-gray-100 shadow-sm flex">
                    <button @click="filter = 'pending'" 
                            class="px-4 py-2 rounded-lg text-sm font-black transition-all"
                            :class="filter === 'pending' ? 'bg-primary text-white shadow-md' : 'text-gray-400 hover:text-gray-600'">
                        PENDING
                    </button>
                    <button @click="filter = 'all'" 
                            class="px-4 py-2 rounded-lg text-sm font-black transition-all"
                            :class="filter === 'all' ? 'bg-primary text-white shadow-md' : 'text-gray-400 hover:text-gray-600'">
                        ALL
                    </button>
                </div>

                <div class="flex items-center gap-2 bg-white px-4 py-2 rounded-full shadow-sm border border-gray-100">
                    <span class="relative flex h-2.5 w-2.5">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
                    </span>
                    <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest">LIVE</span>
                </div>
            </div>
        </header>

        <!-- Loading State -->
        <div v-if="loading && orders.length === 0" class="flex flex-col items-center justify-center py-32 opacity-50">
            <div class="animate-spin rounded-full h-10 w-10 border-4 border-gray-200 border-t-primary mb-4"></div>
            <p class="font-bold text-gray-400 tracking-wide text-sm">CONNECTING TO KITCHEN...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredOrders.length === 0" class="flex flex-col items-center justify-center py-32 text-center animate-scale-in">
            <div class="size-24 rounded-full bg-surface-light flex items-center justify-center mb-6 shadow-sm border border-white text-4xl">☕️</div>
            <h2 class="text-2xl font-black text-primary mb-2">All Caught Up!</h2>
            <p class="text-gray-400 font-medium">No pending orders right now.</p>
        </div>

        <!-- Orders Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
            <TransitionGroup name="list">
                <div v-for="order in filteredOrders" :key="order.id" 
                     class="bg-surface-light rounded-[24px] p-5 shadow-sm border border-gray-100 flex flex-col h-full relative overflow-hidden group hover:shadow-md transition-all duration-300 transform-gpu">
                    
                    <!-- Card Header: Pickup Code -->
                    <div class="flex justify-between items-start mb-5 border-b border-dashed border-gray-100 pb-3">
                        <div class="flex flex-col">
                            <span class="text-5xl font-black text-primary tracking-tighter tabular-nums text-shadow-sm">
                                #{{ order.pickup_code || order.order_no?.slice(-4) || order.id }}
                            </span>
                            <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">
                                {{ new Date(order.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}
                            </span>
                        </div>
                        <div class="px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border" :class="getStatusColor(order.status)">
                            {{ order.status }}
                        </div>
                    </div>

                    <!-- Items List -->
                    <div class="flex-1 space-y-3 mb-6 overflow-y-auto max-h-[400px] no-scrollbar">
                        <div v-for="(item, idx) in order.items" :key="idx" class="flex flex-col gap-1">
                             <div class="flex justify-between items-baseline">
                                 <span class="font-bold text-gray-900 text-lg leading-tight">{{ item.item_name }}</span>
                                 <span class="text-xs font-bold text-gray-300">x1</span>
                             </div>
                             
                             <!-- Spec Tags (The Highlighter) -->
                             <div v-if="parseSpecs(item).length > 0" class="flex flex-wrap gap-1.5 mt-1">
                                 <span v-for="[key, val] in parseSpecs(item)" :key="key" 
                                       class="px-2 py-0.5 rounded-[6px] bg-red-50 border border-red-100 text-[11px] font-black text-red-600 uppercase tracking-wide">
                                     {{ val }}
                                 </span>
                             </div>
                        </div>
                    </div>

                    <!-- Action Button -->
                    <button v-if="order.status !== 'completed'" @click="completeOrder(order.id)" 
                            class="w-full py-4 bg-primary text-white rounded-2xl font-black text-lg shadow-lg shadow-primary/20 active:scale-95 transition-all flex items-center justify-center gap-2 group-hover:bg-[#0d3329]">
                        <span class="material-symbols-rounded">check_circle</span>
                        COMPLETE
                    </button>
                    <div v-else class="w-full py-4 bg-gray-50 text-gray-400 rounded-2xl font-black text-lg border border-gray-100 flex items-center justify-center gap-2">
                        <span class="material-symbols-rounded">done_all</span>
                        DONE
                    </div>
                </div>
            </TransitionGroup>
        </div>
    </div>
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
  transform: scale(0.9);
}
.list-leave-active {
  position: absolute;
}
.text-shadow-sm {
    text-shadow: 0 1px 2px rgba(16, 62, 50, 0.1);
}
</style>
