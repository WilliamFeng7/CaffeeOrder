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
const now = ref(new Date());
let pollInterval: any = null;
let timeInterval: any = null;

const fetchOrders = async () => {
    try {
        orders.value = await api.getAllOrders();
        loading.value = false;
    } catch (e: any) {
        if (e.response?.status === 401) {
            router.push('/login');
        }
    }
};

const completeOrder = async (orderId: number) => {
    try {
        await api.updateOrderStatus(orderId, 'completed');
        toast.success('✓ 制作完成');
        fetchOrders();
    } catch { toast.error('操作失败'); }
};

onMounted(() => {
    fetchOrders();
    pollInterval = setInterval(fetchOrders, 2000);
    timeInterval = setInterval(() => { now.value = new Date(); }, 1000);
});

onUnmounted(() => {
    clearInterval(pollInterval);
    clearInterval(timeInterval);
});

const filtered = computed(() => {
    const sorted = [...orders.value].sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    return filter.value === 'all' ? sorted : sorted.filter(o => ['created', 'processing'].includes(o.status));
});

const pendingCount = computed(() => orders.value.filter(o => ['created', 'processing'].includes(o.status)).length);

// Logic remains the same
const waitMins = (t: string) => Math.floor((now.value.getTime() - new Date(t).getTime()) / 60000);
const urgency = (t: string) => { const m = waitMins(t); return m >= 5 ? 'critical' : m >= 3 ? 'warning' : 'normal'; };
const formatTime = (t: string) => new Date(t).toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit'});

const parseSpec = (item: any) => {
    if (!item.spec) return {};
    try { return typeof item.spec === 'string' ? JSON.parse(item.spec) : item.spec; }
    catch { return {}; }
};

const temp = (item: any) => {
    const t = (parseSpec(item).temperature || parseSpec(item).temp || 'hot').toString().toLowerCase();
    return t.includes('ice') || t.includes('冰') || t.includes('cold') ? 'iced' : 'hot';
};

const size = (item: any) => {
    const s = (parseSpec(item).size || 'regular').toString().toLowerCase();
    return s.includes('large') || s.includes('大') ? 'large' : 'regular';
};

const sugar = (item: any) => parseInt((parseSpec(item).sugar || '100').toString().replace(/[^\d]/g, '')) || 100;

const pickup = (o: Order) => o.pickup_code || o.order_no?.slice(-4) || `${o.id}`;
</script>

<template>
    <div class="kds bg-background-light min-h-screen font-sans text-text-main flex p-6 gap-6 overflow-hidden relative">
        <!-- Floating Glass Sidebar -->
        <aside class="w-24 h-full bg-white/80 backdrop-blur-xl rounded-[40px] shadow-[0_20px_40px_-5px_rgba(0,0,0,0.05)] border border-white/50 flex flex-col items-center py-8 gap-8 z-50 transition-all duration-500 hover:shadow-[0_30px_60px_-10px_rgba(0,0,0,0.1)]">
            <!-- Brand -->
            <div class="size-14 bg-gradient-to-br from-primary to-primary-light rounded-[20px] flex items-center justify-center shadow-lg shadow-primary/30 transform transition hover:scale-105">
                <span class="material-symbols-rounded text-white text-3xl">local_cafe</span>
            </div>
            
            <!-- Nav -->
            <nav class="flex-1 flex flex-col gap-4 w-full px-2">
                <button 
                    @click="filter = 'pending'"
                    :class="['w-full aspect-square rounded-[24px] flex flex-col items-center justify-center gap-1 transition-all duration-300 relative group', filter === 'pending' ? 'bg-primary text-white shadow-xl shadow-primary/30' : 'text-text-sub hover:bg-gray-100']"
                >
                    <span class="material-symbols-rounded text-2xl" :class="{ 'filled': filter === 'pending' }">pending_actions</span>
                    <span class="text-[9px] font-bold tracking-wider uppercase">Prep</span>
                    <span v-if="pendingCount" class="absolute top-2 right-2 size-2.5 bg-red-500 rounded-full border-2 border-white"></span>
                </button>

                <button 
                    @click="filter = 'all'"
                    :class="['w-full aspect-square rounded-[24px] flex flex-col items-center justify-center gap-1 transition-all duration-300 relative group', filter === 'all' ? 'bg-primary text-white shadow-xl shadow-primary/30' : 'text-text-sub hover:bg-gray-100']"
                >
                    <span class="material-symbols-rounded text-2xl" :class="{ 'filled': filter === 'all' }">receipt_long</span>
                    <span class="text-[9px] font-bold tracking-wider uppercase">All</span>
                </button>
            </nav>

            <!-- Status -->
            <div class="flex flex-col items-center gap-2">
                <div class="size-3 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
                <span class="text-[10px] font-bold text-green-600 tracking-widest opacity-80">LIVE</span>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 flex flex-col h-full overflow-hidden">
            <!-- Header -->
            <header class="flex justify-between items-end mb-8 px-4">
                <div>
                    <h1 class="font-serif text-5xl font-bold text-text-main mb-2 tracking-tight">
                        {{ filter === 'pending' ? 'In Preparation' : 'All Orders' }}
                    </h1>
                    <div class="flex items-center gap-2 text-text-sub font-medium">
                        <span class="h-1.5 w-1.5 rounded-full bg-secondary"></span>
                        <span class="tracking-widest uppercase text-xs font-bold">{{ filtered.length }} ORDERS ACTIVE</span>
                    </div>
                </div>
                <div class="text-Right">
                    <div class="font-serif text-4xl text-text-sub opacity-30 font-medium">{{ now.toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'}) }}</div>
                </div>
            </header>

            <!-- Loading -->
            <div v-if="loading" class="flex-1 flex items-center justify-center">
                <div class="size-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
            </div>

            <!-- Empty State -->
            <div v-else-if="!filtered.length" class="flex-1 flex flex-col items-center justify-center text-text-sub opacity-50">
                <span class="material-symbols-rounded text-8xl mb-4 text-gray-300">check_circle</span>
                <p class="font-serif text-2xl italic">All caught up</p>
            </div>

            <!-- Grid -->
            <div v-else class="grid grid-cols-[repeat(auto-fill,minmax(350px,1fr))] gap-6 overflow-y-auto pb-20 px-4 scroll-smooth-touch no-scrollbar content-start">
                <TransitionGroup name="slide-up-content">
                    <article 
                        v-for="o in filtered" 
                        :key="o.id"
                        class="bg-white rounded-[40px] p-6 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.05)] border border-white/50 transition-all duration-400 ease-luxury hover:transform hover:-translate-y-1 hover:shadow-[0_25px_50px_-15px_rgba(0,0,0,0.1)] flex flex-col gap-6 relative overflow-hidden group"
                        :class="{ 'opacity-60': o.status === 'completed' }"
                    >
                        <!-- Status Bar -->
                        <div class="flex justify-between items-center">
                             <div :class="['px-4 py-1.5 rounded-full flex items-center gap-2 text-xs font-black uppercase tracking-wider', 
                                o.status === 'completed' ? 'bg-green-50 text-green-700' :
                                urgency(o.created_at) === 'critical' ? 'bg-red-50 text-red-600 animate-pulse' :
                                urgency(o.created_at) === 'warning' ? 'bg-orange-50 text-orange-600' :
                                'bg-blue-50 text-blue-600'
                             ]">
                                <span class="material-symbols-rounded text-base">
                                    {{ o.status === 'completed' ? 'check' : 
                                       urgency(o.created_at) === 'critical' ? 'priority_high' : 'schedule' }}
                                </span>
                                {{ o.status === 'completed' ? 'DONE' : 
                                   urgency(o.created_at) === 'critical' ? 'URGENT' :
                                   urgency(o.created_at) === 'warning' ? 'LATE' : 'NEW' }}
                             </div>
                             <span class="text-xs font-bold text-text-sub/60">{{ formatTime(o.created_at) }}</span>
                        </div>

                        <!-- Pickup Number (The Hero) -->
                        <div class="text-center py-2">
                             <h2 class="font-sans text-8xl font-black text-text-main tracking-tighter leading-none">
                                {{ pickup(o) }}
                             </h2>
                             <span class="text-[10px] uppercase tracking-[0.2em] font-bold text-text-sub opacity-60">Pickup Number</span>
                        </div>

                        <!-- Items List -->
                        <div class="space-y-3">
                            <div v-for="(it, i) in o.items" :key="i" class="bg-gray-50 rounded-[20px] p-4 flex flex-col gap-2">
                                <div class="flex justify-between items-start">
                                    <span class="font-bold text-text-main text-lg">{{ it.item_name }}</span>
                                    <span v-if="(it.quantity || 1) > 1" class="bg-secondary text-[#0C1F1A] text-xs font-black px-2 py-1 rounded-lg">x{{ it.quantity }}</span>
                                </div>
                                
                                <div class="flex flex-wrap gap-2">
                                    <!-- Temp Tag -->
                                    <span :class="['px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider flex items-center gap-1', temp(it) === 'hot' ? 'bg-red-100 text-red-700' : 'bg-cyan-100 text-cyan-700']">
                                        <span class="material-symbols-rounded text-[14px]">{{ temp(it) === 'hot' ? 'local_fire_department' : 'ac_unit' }}</span>
                                        {{ temp(it) === 'hot' ? 'Hot' : 'Iced' }}
                                    </span>
                                    <!-- Size Tag -->
                                    <span :class="['px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-purple-100 text-purple-700']">
                                        {{ size(it) === 'large' ? 'Large' : 'Regular' }}
                                    </span>
                                    <!-- Sugar Tag -->
                                    <span class="px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-orange-100 text-orange-700">
                                        {{ sugar(it) }}% Sugar
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- Action Button -->
                        <button 
                            v-if="o.status !== 'completed'"
                            @click="completeOrder(o.id)"
                            class="w-full bg-primary text-white h-14 rounded-[24px] font-bold text-lg shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all duration-300 ease-luxury flex items-center justify-center gap-2 mt-auto"
                        >
                            <span class="material-symbols-rounded">check</span>
                            Complete
                        </button>
                        <div v-else class="w-full h-14 rounded-[24px] bg-green-100 text-green-700 flex items-center justify-center gap-2 font-bold cursor-default opacity-50">
                            <span class="material-symbols-rounded">done_all</span>
                            Completed
                        </div>

                    </article>
                </TransitionGroup>
            </div>
        </main>

        <!-- Background Noise -->
        <div class="fixed inset-0 pointer-events-none opacity-20 z-0 mix-blend-overlay" style="background-image: url('data:image/svg+xml,...');"></div>
    </div>
</template>

<style scoped>
/* Scoped styles mostly handled by Tailwind classes now for better consistency */
</style>
