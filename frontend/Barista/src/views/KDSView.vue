
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
    if (status === 'created') return 'bg-yellow-100/50 text-yellow-800 border-yellow-200';
    if (status === 'processing') return 'bg-blue-100/50 text-blue-800 border-blue-200';
    if (status === 'completed') return 'bg-green-100/50 text-green-800 border-green-200';
    return 'bg-gray-100 text-gray-600';
};
</script>

<template>
    <div class="min-h-screen p-4 md:p-8 pb-24 animate-fade-in bg-[#F5F7F6]">
        <!-- Header -->
        <header class="flex flex-col md:flex-row justify-between items-center mb-10 sticky top-0 md:top-4 z-20 transition-all duration-300">
            <!-- Glassy background container for header content -->
            <div class="w-full bg-white/70 backdrop-blur-xl border border-white/60 shadow-sm rounded-[32px] px-8 py-5 flex justify-between items-center">
                <div class="flex items-center gap-4">
                     <div class="size-14 bg-primary/5 rounded-2xl flex items-center justify-center border border-primary/10">
                        <span class="material-symbols-rounded text-primary text-3xl">soup_kitchen</span>
                     </div>
                     <div>
                        <h1 class="text-3xl font-serif font-black text-text-main tracking-tight italic">Barista KDS</h1>
                        <p class="text-sm text-text-sub font-bold tracking-widest uppercase">Live Orders</p>
                     </div>
                </div>
                
                <div class="flex items-center gap-4">
                     <!-- Filter Toggle -->
                    <div class="bg-gray-100/80 p-1.5 rounded-2xl flex border border-gray-200/50">
                        <button @click="filter = 'pending'" 
                                class="px-6 py-3 rounded-xl text-sm font-black transition-all duration-300 ease-spring"
                                :class="filter === 'pending' ? 'bg-white text-primary shadow-md shadow-gray-200 scale-100' : 'text-gray-400 hover:text-gray-600 scale-95'">
                            PENDING
                        </button>
                        <button @click="filter = 'all'" 
                                class="px-6 py-3 rounded-xl text-sm font-black transition-all duration-300 ease-spring"
                                :class="filter === 'all' ? 'bg-white text-primary shadow-md shadow-gray-200 scale-100' : 'text-gray-400 hover:text-gray-600 scale-95'">
                            ALL ORDERS
                        </button>
                    </div>

                    <div class="hidden md:flex items-center gap-2 bg-white/80 px-4 py-2 rounded-full shadow-sm border border-white/60">
                        <span class="relative flex h-2.5 w-2.5">
                          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
                        </span>
                        <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest">Connected</span>
                    </div>
                </div>
            </div>
        </header>

        <!-- Loading State -->
        <div v-if="loading && orders.length === 0" class="flex flex-col items-center justify-center py-32 opacity-60">
            <div class="animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-primary mb-6"></div>
            <p class="font-bold text-gray-400 tracking-widest text-sm uppercase">Syncing with Kitchen...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredOrders.length === 0" class="flex flex-col items-center justify-center py-32 text-center animate-scale-in">
            <div class="size-32 rounded-[40px] bg-white border border-gray-100 flex items-center justify-center mb-8 shadow-xl shadow-gray-200/50 rotate-3">
                <span class="material-symbols-rounded text-6xl text-primary/20">check_circle</span>
            </div>
            <h2 class="text-3xl font-serif font-bold text-text-main mb-3">All Caught Up!</h2>
            <p class="text-text-sub font-medium max-w-xs mx-auto">No pending orders at the moment. Take a break ☕️</p>
        </div>

        <!-- Orders Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
            <TransitionGroup name="list">
                <div v-for="order in filteredOrders" :key="order.id" 
                     class="bg-white rounded-[32px] p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100 flex flex-col h-full relative overflow-hidden group hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-500 ease-luxury">
                    
                    <!-- Card Header: Pickup Code -->
                    <div class="flex justify-between items-start mb-6 pb-4 border-b border-gray-50">
                        <div class="flex flex-col">
                            <span class="text-6xl font-black text-text-main tracking-tighter tabular-nums leading-none">
                                #{{ order.pickup_code || order.order_no?.slice(-4) || order.id }}
                            </span>
                            <span class="text-[11px] font-bold text-gray-400 uppercase tracking-widest mt-2 pl-1">
                                {{ new Date(order.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}
                            </span>
                        </div>
                        <div class="px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider border" :class="getStatusColor(order.status)">
                            {{ order.status }}
                        </div>
                    </div>

                    <!-- Items List -->
                    <div class="flex-1 space-y-4 mb-8 overflow-y-auto max-h-[400px] no-scrollbar pr-2">
                        <div v-for="(item, idx) in order.items" :key="idx" class="flex flex-col gap-1.5 p-3 rounded-2xl bg-gray-50/50 hover:bg-gray-50 transition-colors">
                             <div class="flex justify-between items-start">
                                 <span class="font-bold text-text-main text-lg leading-tight">{{ item.item_name }}</span>
                                 <span class="text-sm font-black text-gray-300 bg-white px-2 py-0.5 rounded-md shadow-sm">x1</span>
                             </div>
                             
                             <!-- Spec Tags -->
                             <div v-if="parseSpecs(item).length > 0" class="flex flex-wrap gap-2 mt-1">
                                 <span v-for="[key, val] in parseSpecs(item)" :key="key" 
                                       class="px-2.5 py-1 rounded-[8px] bg-secondary/10 border border-secondary/20 text-[11px] font-bold text-secondary-content uppercase tracking-wide">
                                     {{ val }}
                                 </span>
                             </div>
                        </div>
                    </div>

                    <!-- Action Button -->
                    <button v-if="order.status !== 'completed'" @click="completeOrder(order.id)" 
                            class="w-full py-5 bg-primary text-white rounded-[24px] font-black text-lg shadow-xl shadow-primary/20 active:scale-95 transition-all flex items-center justify-center gap-3 group-hover:bg-[#0d3329] relative overflow-hidden">
                         <!-- Shine effect -->
                         <div class="absolute inset-0 translate-x-[-100%] group-hover:animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent z-0"></div>
                        <span class="material-symbols-rounded z-10">check_circle</span>
                        <span class="z-10">COMPLETE ORDER</span>
                    </button>
                    <div v-else class="w-full py-5 bg-gray-50 text-gray-300 rounded-[24px] font-black text-lg border border-gray-100 flex items-center justify-center gap-3">
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
  transform: scale(0.95);
}
.list-leave-active {
  position: absolute;
}
/* Hide scrollbar for Chrome, Safari and Opera */
.no-scrollbar::-webkit-scrollbar {
    display: none;
}
/* Hide scrollbar for IE, Edge and Firefox */
.no-scrollbar {
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
}
</style>
