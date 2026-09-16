<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { api } from '../api';
import { useToastStore } from '../stores/toast';

const orders = ref<any[]>([]);
const loading = ref(true);
const filter = ref<'all' | 'pending' | 'completed'>('all');
const showDetailModal = ref(false);
const selectedOrder = ref<any>(null);
const toast = useToastStore();

const fetchOrders = async () => {
    loading.value = true;
    try {
        orders.value = await api.getAllOrders();
    } catch (e: any) {
        console.error(e);
        toast.error('加载订单失败: ' + (e.response?.data?.detail || e.message));
    } finally {
        loading.value = false;
    }
};

const filteredOrders = computed(() => {
    if (filter.value === 'all') return orders.value;
    if (filter.value === 'pending') {
        return orders.value.filter(o => ['created', 'processing', 'ready'].includes(o.status));
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
  <div class="space-y-6 animate-fade-in">
     <div class="flex justify-between items-center">
         <h1 class="text-3xl font-black text-primary tracking-tight">订单管理</h1>
         
         <div class="flex bg-white p-1 rounded-xl border border-gray-100 shadow-sm">
             <button @click="filter = 'all'" class="px-4 py-2 rounded-lg text-sm font-bold transition-all" :class="filter === 'all' ? 'bg-primary text-white shadow-md' : 'text-gray-400 hover:text-gray-600'">全部</button>
             <button @click="filter = 'pending'" class="px-4 py-2 rounded-lg text-sm font-bold transition-all" :class="filter === 'pending' ? 'bg-primary text-white shadow-md' : 'text-gray-400 hover:text-gray-600'">待处理</button>
             <button @click="filter = 'completed'" class="px-4 py-2 rounded-lg text-sm font-bold transition-all" :class="filter === 'completed' ? 'bg-primary text-white shadow-md' : 'text-gray-400 hover:text-gray-600'">已完成</button>
         </div>
     </div>

     <!-- Orders List -->
     <div class="space-y-4">
         <div v-for="order in filteredOrders" :key="order.id" class="bg-white p-6 rounded-[28px] shadow-sm border border-gray-100 flex items-center justify-between group hover:shadow-md transition-all duration-300">
             
             <!-- Left Info -->
             <div class="flex items-center gap-6 cursor-pointer" @click="viewDetails(order)">
                 <div class="size-16 rounded-2xl flex items-center justify-center font-black text-xl transition-colors overflow-hidden" 
                      :class="order.status === 'completed' ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'">
                     <span class="scale-75">{{ order.order_no ? order.order_no.slice(-4) : order.id }}</span>
                 </div>
                 
                 <div>
                     <p class="font-bold text-gray-900 text-lg group-hover:text-primary transition-colors">{{ order.user || 'Guest/Deleted' }}</p>
                     <p class="text-xs text-gray-400 font-mono mt-0.5">{{ new Date(order.created_at).toLocaleString() }}</p>
                     <div class="flex items-center gap-2 mt-2">
                         <span class="px-2 py-0.5 rounded text-[10px] font-black uppercase bg-gray-100 text-gray-500">堂食</span>
                         <span class="font-black text-primary">¥{{ order.total.toFixed(2) }}</span>
                         <span class="text-xs text-blue-500 font-bold ml-2 hover:underline">查看详情</span>
                     </div>
                 </div>
             </div>

             <!-- Right Actions -->
             <div class="flex items-center gap-4">
                 <div v-if="order.status !== 'completed'">
                     <button @click="handleStatusChange(order.id, 'completed')" class="px-6 py-3 bg-[#103E32] text-white rounded-xl font-bold text-sm shadow-lg shadow-primary/20 hover:scale-105 transition-transform flex items-center gap-2">
                         <span class="material-symbols-rounded">check</span>
                         完成订单
                     </button>
                 </div>
                 <div v-else class="text-green-600 font-bold flex items-center gap-2 px-6 py-3 bg-green-50 rounded-xl">
                      <span class="material-symbols-rounded">done_all</span>
                      已完成
                 </div>
             </div>

         </div>
         
         <div v-if="filteredOrders.length === 0" class="text-center py-20 text-gray-400">
             <span class="material-symbols-rounded text-6xl opacity-30">inbox</span>
             <p class="mt-4 font-bold">暂无订单</p>
         </div>
     </div>

     <!-- Detail Modal -->
     <Teleport to="body">
     <div v-if="showDetailModal && selectedOrder" class="fixed inset-0 z-50 flex items-center justify-center p-4">
         <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showDetailModal = false"></div>
         <div class="bg-white w-full max-w-lg rounded-[32px] p-8 relative z-10 shadow-2xl animate-scale-in max-h-[90vh] overflow-y-auto">
             <div class="flex justify-between items-start mb-6">
                 <div>
                     <h3 class="text-2xl font-black text-primary">订单 #{{ selectedOrder.order_no }}</h3>
                     <p class="text-sm text-gray-400">{{ new Date(selectedOrder.created_at).toLocaleString() }}</p>
                 </div>
                 <button @click="showDetailModal = false" class="size-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200">
                     <span class="material-symbols-rounded">close</span>
                 </button>
             </div>

             <div class="space-y-4">
                 <div v-for="(item, idx) in selectedOrder.items" :key="idx" class="flex gap-4">
                     <div class="size-16 rounded-xl bg-gray-100 bg-cover bg-center shrink-0" :style="{ backgroundImage: `url(${item.image_url})` }"></div>
                     <div class="flex-1">
                         <div class="flex justify-between">
                             <h4 class="font-bold text-gray-900">{{ item.item_name }}</h4>
                             <span class="font-bold text-gray-900">¥{{ (item.price_snap / 100).toFixed(2) }}</span>
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
                 <span class="text-sm font-bold text-gray-400 uppercase tracking-widest">总金额</span>
                 <span class="text-3xl font-black text-primary">¥{{ selectedOrder.total.toFixed(2) }}</span>
             </div>
         </div>
     </div>
     </Teleport>
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.4s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.animate-scale-in { animation: scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
@keyframes scaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
</style>
