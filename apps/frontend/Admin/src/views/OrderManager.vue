<script setup lang="ts">
import AppIcon from '@shared/components/AppIcon.vue';
import AppModal from '@shared/components/AppModal.vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
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
    created: { label: '待制作', cls: 'text-secondary-content' },
    processing: { label: '制作中', cls: 'text-text-main' },
    ready: { label: '待取餐', cls: 'text-primary' },
    completed: { label: '已完成', cls: 'text-text-sub' },
    refunded: { label: '已退款', cls: 'text-text-sub' },
};
const statusMeta = (status: string) => STATUS_META[status] ?? { label: status, cls: 'text-text-sub' };

const filterOptions = [
    { value: 'all' as const, label: '全部' },
    { value: 'pending' as const, label: '待处理' },
    { value: 'completed' as const, label: '已完成' },
];

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
  <div class="space-y-6">
     <div class="flex flex-wrap items-end justify-between gap-4 animate-slide-up-content">
         <div>
             <p class="eyebrow">{{ filteredOrders.length }} 笔订单</p>
             <h1 class="mt-2 font-serif text-[34px] font-medium leading-tight tracking-[-0.015em]">订单管理</h1>
         </div>
         <SlidingTabs v-model="filter" :options="filterOptions" variant="segment" size="sm" label="订单筛选" />
     </div>

     <!-- Loading -->
     <div v-if="loading" class="card divide-y divide-line" aria-hidden="true">
         <div v-for="i in 5" :key="i" class="px-6 py-5 flex items-center gap-5">
             <div class="size-12 rounded-tile bg-cream animate-pulse"></div>
             <div class="flex-1 space-y-2">
                 <div class="h-3.5 w-40 rounded-full bg-cream animate-pulse"></div>
                 <div class="h-3 w-64 rounded-full bg-cream animate-pulse"></div>
             </div>
         </div>
     </div>

     <!-- Orders (the list crossfades when the filter changes) -->
     <Transition v-else name="page" mode="out-in">
     <div :key="filter" class="card overflow-hidden">
         <ul v-if="filteredOrders.length" class="divide-y divide-line stagger-in">
             <li v-for="order in filteredOrders" :key="order.id" class="group px-6 py-4 flex items-center gap-5 hover:bg-background-light transition-colors duration-color">
                 <!-- Pickup number: what the customer and the barista call out -->
                 <button type="button" class="flex items-center gap-5 min-w-0 flex-1 text-left" @click="viewDetails(order)">
                     <span class="w-14 shrink-0">
                         <span class="block eyebrow !text-[10px]">取餐号</span>
                         <span class="block mt-1 font-serif text-[26px] font-medium leading-none tabular-nums">{{ order.pickup_number ?? '—' }}</span>
                     </span>
                     <span class="min-w-0">
                         <span class="flex items-center gap-2.5 min-w-0">
                             <span class="text-[15px] font-medium truncate">{{ customerName(order) }}</span>
                             <span class="flex items-center gap-1.5 text-[12px] font-medium shrink-0" :class="statusMeta(order.status).cls">
                                 <span class="dot" aria-hidden="true"></span>
                                 {{ statusMeta(order.status).label }}
                             </span>
                         </span>
                         <span class="block mt-1 text-[12px] text-text-sub tabular-nums truncate">
                             {{ new Date(order.created_at).toLocaleString() }}
                             <span class="mx-1">·</span>
                             订单 {{ order.id }}
                             <span class="ml-2 text-text-main opacity-0 group-hover:opacity-100 transition-opacity duration-color">查看详情 →</span>
                         </span>
                     </span>
                 </button>

                 <span class="font-serif text-[18px] font-medium tabular-nums shrink-0">¥{{ order.total.toFixed(2) }}</span>

                 <div class="w-[108px] flex justify-end shrink-0">
                     <button
                         v-if="ACTIVE.includes(order.status)"
                         type="button"
                         @click="handleStatusChange(order.id, 'completed')"
                         class="btn btn-outline btn-sm"
                     >
                         <AppIcon name="check" class="text-base" />
                         完成
                     </button>
                     <span v-else-if="order.status === 'completed'" class="text-[13px] text-text-sub flex items-center gap-1.5">
                         <AppIcon name="checks" weight="light" class="text-base" />
                         已完成
                     </span>
                     <span v-else class="text-[13px] text-text-sub flex items-center gap-1.5">
                         <AppIcon name="undo" weight="light" class="text-base" />
                         {{ statusMeta(order.status).label }}
                     </span>
                 </div>
             </li>
         </ul>

         <div v-else class="py-20 flex flex-col items-center gap-2 text-text-sub">
             <AppIcon name="tray" weight="light" class="text-3xl" />
             <p class="text-[13px]">暂无订单</p>
         </div>
     </div>
     </Transition>

     <!-- Detail -->
     <AppModal
        :open="showDetailModal && !!selectedOrder"
        :title="selectedOrder ? `取餐号 ${selectedOrder.pickup_number ?? '—'}` : ''"
        :subtitle="selectedOrder ? `${customerName(selectedOrder)} · ${new Date(selectedOrder.created_at).toLocaleString()}` : ''"
        @close="showDetailModal = false"
     >
         <template v-if="selectedOrder">
             <p class="-mt-3 mb-5 font-mono text-[11px] text-text-sub">{{ selectedOrder.order_no }}</p>
             <ul class="divide-y divide-line border-y border-line">
                 <li v-for="(item, idx) in selectedOrder.items" :key="idx" class="py-4 flex gap-4">
                     <div class="size-14 rounded-tile bg-cream bg-cover bg-center shrink-0" :style="{ backgroundImage: `url(${item.image_url})` }"></div>
                     <div class="flex-1 min-w-0">
                         <div class="flex justify-between gap-3">
                             <p class="text-[15px] font-medium">{{ item.item_name }} <span v-if="item.quantity > 1" class="text-text-sub">×{{ item.quantity }}</span></p>
                             <span class="text-[14px] tabular-nums">¥{{ (item.price_snap * (item.quantity || 1) / 100).toFixed(2) }}</span>
                         </div>
                         <div v-if="item.spec" class="mt-1.5 flex flex-wrap gap-1.5">
                             <span v-for="(val, key) in item.spec" :key="key" class="chip chip-quiet">{{ key }}: {{ val }}</span>
                         </div>
                     </div>
                 </li>
             </ul>
             <div class="mt-5 flex items-baseline justify-between">
                 <span class="eyebrow">总金额</span>
                 <span class="font-serif text-[30px] font-medium tabular-nums">¥{{ selectedOrder.total.toFixed(2) }}</span>
             </div>
         </template>
     </AppModal>
  </div>
</template>
