<script setup lang="ts">
/**
 * HistoryView.vue
 * 
 * 历史订单视图组件 (History View Component).
 * 
 * 主要功能 (Core Features):
 * 1. 历史记录 (Order History): 从 LocalStorage 或 API 加载历史订单。
 * 2. 订单展示 (Order List): 显示订单时间、取餐号、总价和包含的商品。
 * 3. 详情查看 (Details): 展示订单 UUID 和商品详情 (糖度、杯型)。
 * 
 * 注意:
 * 部分历史记录查看功能已整合至 SettingsView，本组件保留作为独立入口或备用视图。
 */

import AppIcon from '@shared/components/AppIcon.vue';
import { ref, computed, onMounted } from 'vue';
import { TRANSLATIONS } from '../data';
import type { Order, ViewState, Language } from '../types';

// --- Props & Events ---
const props = defineProps<{
  lang: Language; // 当前语言
}>();

const emit = defineEmits<{
  (e: 'navigate', view: ViewState): void; // 导航请求
}>();

// --- 状态定义 (State Definitions) ---

// 订单列表数据
const orders = ref<Order[]>([]);

// 计算属性: 获取翻译
const t = computed(() => TRANSLATIONS[props.lang]);

// --- 生命周期 (Lifecycle) ---

/**
 * 组件挂载时加载历史记录
 * 目前逻辑为从 LocalStorage 读取 'downtown_cafe_history'。
 * 生产环境应替换为 API 调用 (如 GET /orders/me)。
 */
onMounted(() => {
  try {
    const stored = sessionStorage.getItem('otia_cafe_history');
    if (stored) {
      // 解析 JSON
      const parsedOrders: Order[] = JSON.parse(stored);
      // 按日期降序排序 (最新的在最前)
      parsedOrders.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      orders.value = parsedOrders;
    }
  } catch (e) {
    console.error("Failed to load history", e);
  }
});

</script>

<template>
  <div class="flex flex-col h-full bg-background-light">
     <!-- Header Navigation -->
     <!-- 顶部导航栏 -->
     <header class="flex items-center p-6 pb-2 shrink-0">
       <button @click="emit('navigate', 'order')" class="flex items-center justify-center size-12 rounded-full bg-white shadow-sm active:bg-gray-50 active:scale-75 transition-all duration-500 ease-luxury outline-none">
          <AppIcon name="arrow-left" class="text-text-main" />
       </button>
       <h1 class="text-xl font-bold ml-4 text-text-main">{{ t.orderHistory }}</h1>
     </header>

     <!-- Scrollable Main Content -->
     <main class="flex-1 overflow-y-auto p-6 pt-4 space-y-4 no-scrollbar">
       
       <!-- Empty State -->
       <!-- 空状态展示 -->
       <div v-if="orders.length === 0" class="flex flex-col items-center justify-center h-64 text-text-sub">
          <div class="size-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
             <AppIcon name="receipt" class="text-3xl opacity-50" />
          </div>
          <p class="font-medium">{{ t.noOrders }}</p>
          <button 
             @click="emit('navigate', 'order')"
             class="mt-4 text-primary-content bg-primary px-6 py-2 rounded-full font-bold text-sm active:scale-95 transition-all duration-500 ease-luxury shadow-lg shadow-primary/20"
          >
             {{ t.startOrdering }}
          </button>
       </div>

       <!-- Orders List -->
       <!-- 订单卡片列表 -->
       <div v-else class="space-y-4">
          <div v-for="order in orders" :key="order.id" class="bg-white p-5 rounded-3xl shadow-sm border border-gray-100 pb-2">
             <!-- Order Header Info -->
             <div class="flex justify-between items-start mb-4 pb-4 border-b border-gray-50">
                <div>
                   <!-- Date & Time -->
                   <p class="text-xs text-text-sub font-bold uppercase tracking-wider">
                      {{ new Date(order.date).toLocaleString([], {year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute:'2-digit', second: '2-digit'}) }}
                   </p>
                   <!-- Pickup Number & Short UUID -->
                   <div class="flex gap-2 items-center mt-1">
                       <span class="bg-gray-100 px-1.5 py-0.5 rounded text-[10px] font-black text-gray-500">Pick #{{ order.dailyNumber }}</span>
                       <span class="text-[10px] text-gray-300 font-mono">ID: {{ order.order_no ? order.order_no.slice(0, 8) : '...' }}...</span>
                   </div>
                </div>
                
                <!-- Price & Status -->
                <div class="text-right">
                   <span class="block text-xl font-bold text-text-main">¥{{ order.total.toFixed(2) }}</span>
                   <span class="inline-flex items-center gap-1 text-[10px] font-bold text-green-700 bg-green-100 px-2 py-0.5 rounded-full mt-1">
                      <AppIcon name="check-circle" weight="fill" class="text-[12px]" />
                      {{ t.completed }}
                   </span>
                </div>
             </div>

             <!-- Order Items -->
             <div class="space-y-4">
                <div v-for="(item, idx) in order.items" :key="idx" class="flex items-center justify-between">
                   <div class="flex items-center gap-3">
                      <!-- Item Image -->
                      <div class="size-12 rounded-xl bg-gray-100 bg-cover bg-center shrink-0" :style="{ backgroundImage: `url(${item.image})` }"></div>
                      
                      <!-- Item Details -->
                      <div>
                         <p class="text-sm font-bold text-text-main leading-tight line-clamp-1">
                            {{ lang === 'cn' && item.nameCN ? item.nameCN : item.name }}
                         </p>
                         <p class="text-xs text-text-sub mt-0.5">
                            {{ item.sugar && item.sugar !== 'Regular' ? `${item.sugar}` : '' }}
                         </p>
                      </div>
                   </div>
                   <!-- Quantity -->
                   <span class="text-sm font-bold text-text-main bg-gray-50 px-2 py-1 rounded-md">x{{ item.quantity }}</span>
                </div>
             </div>

             <!-- Full UUID Footer -->
             <div class="mt-4 pt-2 border-t border-gray-50 text-[9px] text-gray-300 font-mono break-all text-center">
                 {{ order.order_no }}
             </div>
          </div>
       </div>
       <div class="h-6"></div>
     </main>
  </div>
</template>
