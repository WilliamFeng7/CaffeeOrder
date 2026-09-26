<script setup lang="ts">
import AppIcon from '@shared/components/AppIcon.vue';
import { ref, onMounted, computed } from 'vue';
import { api, type User } from '../api';
import { useToastStore } from '../stores/toast';

const orders = ref<any[]>([]);
const users = ref<Map<number, User>>(new Map());
const loading = ref(true);
const filter = ref<'all' | 'pending' | 'completed'>('all');
const showDetailModal = ref(false);
const selectedOrder = ref<any>(null);
const toast = useToastStore();

const ACTIVE = ['created', 'processing', 'ready'];

// 状态标签 (Status chips): every lifecycle state gets its own label, instead of
// "not completed" being treated as one bucket (which offered 完成订单 on refunds).
const STATUS_META: Record<string, { label: string; cls: string }> = {
    created: { label: '待制作', cls: 'bg-amber-50 text-amber-700' },
    processing: { label: '制作中', cls: 'bg-indigo-50 text-indigo-700' },
    ready: { label: '待取餐', cls: 'bg-emerald-50 text-emerald-700' },
    completed: { label: '已完成', cls: 'bg-green-50 text-green-700' },
    refunded: { label: '已退款', cls: 'bg-gray-100 text-gray-600' },
};
const statusMeta = (status: string) => STATUS_META[status] ?? { label: status, cls: 'bg-gray-100 text-gray-600' };

const fetchOrders = async () => {
    loading.value = true;
    try {
        // Orders only carry user_id; the user list turns that into a name.
        const [list, userList] = await Promise.all([
            api.getAllOrders(),
            api.getUsers().catch(() => [] as User[]),
        ]);
        orders.value = list;
        users.value = new Map(userList.map(u => [u.id, u]));
    } catch (e: any) {
        console.error(e);
        toast.error('加载订单失败: ' + (e.response?.data?.detail || e.message));
    } finally {
        loading.value = false;
    }
};

const customerName = (order: any) => {
    const u = users.value.get(order.user);
    if (!u) return order.user ? `用户 #${order.user}` : 'Guest/Deleted';
    return u.name || u.username;
};

const filteredOrders = computed(() => {
    if (filter.value === 'all') return orders.value;
    if (filter.value === 'pending') {
        return orders.value.filter(o => ACTIVE.includes(o.status));
    }
    return orders.value.filter(o => o.status === filter.value);
});

const handleStatusChange = async (orderId: number, newStatus: string) => {
    try {
        await api.updateOrderStatus(orderId, newStatus);
        const order = orders.value.find(o => o.id === orderId);
        if (order) order.status = newStatus;
        toast.success('订单状态已更新');
    } catch (e: any) {
        toast.error(e.response?.data?.detail || '状态更新失败');
    }
};

const viewDetails = (order: any) => {
    selectedOrder.value = order;
    showDetailModal.value = true;
};

onMounted(fetchOrders);
</script>

<template>
  <div class="space-y-5 animate-fade-in">
     <div class="flex justify-between items-center gap-4">
         <h1 class="text-3xl font-black text-primary tracking-tight">订单管理</h1>
         
         <div class="flex bg-white p-1 rounded-xl border border-gray-100 shadow-sm">
             <button type="button" @click="filter = 'all'" class="px-4 py-2 rounded-lg text-sm font-bold" :class="filter === 'all' ? 'bg-primary text-white shadow-md' : 'text-gray-500 hover:text-gray-700'">全部</button>
             <button type="button" @click="filter = 'pending'" class="px-4 py-2 rounded-lg text-sm font-bold" :class="filter === 'pending' ? 'bg-primary text-white shadow-md' : 'text-gray-500 hover:text-gray-700'">待处理</button>
             <button type="button" @click="filter = 'completed'" class="px-4 py-2 rounded-lg text-sm font-bold" :class="filter === 'completed' ? 'bg-primary text-white shadow-md' : 'text-gray-500 hover:text-gray-700'">已完成</button>
         </div>
     </div>

     <!-- Loading -->
     <div v-if="loading" class="space-y-3" aria-hidden="true">
         <div v-for="i in 5" :key="i" class="h-[88px] bg-white rounded-[24px] border border-gray-100 relative overflow-hidden">
             <div class="absolute inset-0 bg-gradient-to-r from-transparent via-gray-100/80 to-transparent animate-shimmer"></div>
         </div>
     </div>

     <!-- Orders List -->
     <div v-else class="space-y-3 stagger-in">
         <div v-for="order in filteredOrders" :key="order.id" class="bg-white px-5 py-4 rounded-[24px] shadow-sm border border-gray-100 flex items-center justify-between gap-4 group hover:shadow-md transition-shadow duration-200">
             
             <!-- Left Info -->
             <div class="flex items-center gap-5 cursor-pointer min-w-0" @click="viewDetails(order)">
                 <!-- Pickup number: what the customer and the barista call out -->
                 <div class="size-14 rounded-2xl flex flex-col items-center justify-center shrink-0 bg-[#F2F7F5] text-primary">
                     <span class="text-[9px] font-black uppercase tracking-widest text-gray-500 leading-none">取餐号</span>
                     <span class="text-xl font-black leading-tight tabular-nums">{{ order.pickup_number ?? '—' }}</span>
                 </div>
                 
                 <div class="min-w-0">
                     <div class="flex items-center gap-2 min-w-0">
                         <p class="font-bold text-gray-900 text-base truncate group-hover:text-primary transition-colors">{{ customerName(order) }}</p>
                         <span v-if="ACTIVE.includes(order.status)" class="px-2 py-0.5 rounded-md text-[11px] font-black shrink-0" :class="statusMeta(order.status).cls">{{ statusMeta(order.status).label }}</span>
                     </div>
                     <p class="text-xs text-gray-500 font-mono mt-1 truncate">
                         {{ new Date(order.created_at).toLocaleString() }}
                         <span class="mx-1 text-gray-300">·</span>
                         订单 {{ order.id }}
                     </p>
                     <div class="flex items-center gap-2 mt-1.5">
                         <span class="font-black text-primary tabular-nums">¥{{ order.total.toFixed(2) }}</span>
                         <span class="text-xs text-blue-600 font-bold ml-1 hover:underline">查看详情</span>
                     </div>
                 </div>
             </div>

             <!-- Right Actions -->
             <div class="flex items-center gap-4 shrink-0">
                 <button
                     v-if="ACTIVE.includes(order.status)"
                     type="button"
                     @click="handleStatusChange(order.id, 'completed')"
                     class="px-5 py-2.5 bg-[#103E32] text-white rounded-xl font-bold text-sm shadow-lg shadow-primary/20 hover:bg-[#0c3128] flex items-center gap-2"
                 >
                     <AppIcon name="check" class="text-xl" />
                     完成订单
                 </button>
                 <div v-else-if="order.status === 'completed'" class="text-green-700 font-bold text-sm flex items-center gap-2 px-5 py-2.5 bg-green-50 rounded-xl">
                      <AppIcon name="checks" class="text-xl" />
                      已完成
                 </div>
                 <div v-else class="text-gray-600 font-bold text-sm flex items-center gap-2 px-5 py-2.5 bg-gray-100 rounded-xl">
                      <AppIcon name="undo" class="text-xl" />
                      {{ statusMeta(order.status).label }}
                 </div>
             </div>

         </div>
         
         <div v-if="filteredOrders.length === 0" class="text-center py-20 text-gray-500">
             <AppIcon name="tray" class="text-6xl opacity-30" />
             <p class="mt-4 font-bold">暂无订单</p>
         </div>
     </div>

     <!-- Detail Modal -->
     <Teleport to="body">
     <div v-if="showDetailModal && selectedOrder" class="fixed inset-0 z-50 flex items-center justify-center p-4">
         <div class="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fade-in" @click="showDetailModal = false"></div>
         <div class="bg-white w-full max-w-lg rounded-[32px] p-8 relative z-10 shadow-2xl animate-scale-in max-h-[90vh] overflow-y-auto" role="dialog" aria-modal="true">
             <div class="flex justify-between items-start mb-6">
                 <div>
                     <h3 class="text-2xl font-black text-primary">取餐号 {{ selectedOrder.pickup_number ?? '—' }}</h3>
                     <p class="text-sm text-gray-500 mt-1">{{ customerName(selectedOrder) }} · {{ new Date(selectedOrder.created_at).toLocaleString() }}</p>
                     <p class="text-xs text-gray-400 font-mono mt-0.5">{{ selectedOrder.order_no }}</p>
                 </div>
                 <button type="button" @click="showDetailModal = false" aria-label="关闭" class="size-9 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200">
                     <AppIcon name="x" />
                 </button>
             </div>

             <div class="space-y-4">
                 <div v-for="(item, idx) in selectedOrder.items" :key="idx" class="flex gap-4">
                     <div class="size-16 rounded-xl bg-gray-100 bg-cover bg-center shrink-0" :style="{ backgroundImage: `url(${item.image_url})` }"></div>
                     <div class="flex-1">
                         <div class="flex justify-between">
                             <h4 class="font-bold text-gray-900">{{ item.item_name }} <span v-if="item.quantity > 1" class="text-gray-500 font-black">×{{ item.quantity }}</span></h4>
                             <span class="font-bold text-gray-900 tabular-nums">¥{{ (item.price_snap * (item.quantity || 1) / 100).toFixed(2) }}</span>
                         </div>
                         <div class="text-xs text-gray-500 mt-1">
                             <div v-if="item.spec" class="flex flex-wrap gap-1">
                                 <span v-for="(val, key) in item.spec" :key="key" class="bg-gray-100 px-1.5 py-0.5 rounded text-[10px] uppercase">
                                     {{ key }}: {{ val }}
                                 </span>
                             </div>
                         </div>
                     </div>
                 </div>
             </div>
             
             <hr class="my-6 border-dashed border-gray-200">
             
             <div class="flex justify-between items-end">
                 <span class="text-sm font-bold text-gray-500 uppercase tracking-widest">总金额</span>
                 <span class="text-3xl font-black text-primary tabular-nums">¥{{ selectedOrder.total.toFixed(2) }}</span>
             </div>
         </div>
     </div>
     </Teleport>
  </div>
</template>
