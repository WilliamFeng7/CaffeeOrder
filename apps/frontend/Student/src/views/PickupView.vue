<script setup lang="ts">
/**
 * PickupView.vue
 * 
 * 取餐视图组件 (Pickup View Component).
 * 
 * 主要功能 (Core Features):
 * 1. 订单分栏展示 (Tabbed Interface):
 *    - 当前订单 (Current): 展示 "active" 状态的订单 (制作中/待取餐)。
 *    - 历史订单 (History): 展示 "completed" 状态的已完成订单。
 * 2. 状态可视化 (Visual Status): 大号取餐码显示，清晰的状态标签。
 * 3. 实时更新 (Real-time Updates): 通过 props 接收最新的订单列表。
 */

import { ref, computed } from 'vue';
import { TRANSLATIONS } from '../data';
import type { Order, Language } from '../types';

// --- Props & Events ---
const props = defineProps<{
  orders: Order[]; // 全量订单列表数据源
  lang: Language;  // 当前语言
}>();

// --- 状态定义 (State Definitions) ---

// 当前激活的标签页 ('current' 或 'history')
// Active tab state
const activeTab = ref<'current' | 'history'>('current');

// 计算属性: 获取翻译
const t = computed(() => TRANSLATIONS[props.lang]);

// --- 计算属性 (Computed Properties) ---

/**
 * 筛选当前活跃订单
 * 状态为 'active' (包括制作中、待取餐等非终态)
 */
const currentOrders = computed(() => props.orders.filter(o => o.status === 'active'));

/**
 * 筛选历史已完成订单
 * 状态为 'completed'
 */
const pastOrders = computed(() => props.orders.filter(o => o.status === 'completed'));

// --- 辅助方法 (Date Helpers) ---

/**
 * 格式化时间字符串
 * 转换为本地化格式: YYYY/MM/DD HH:mm
 */
const formatTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

</script>

<template>
  <div class="flex flex-col h-full bg-background-light animate-fade-in">
     <!-- Top Header with Segmented Control -->
     <!-- 顶部导航栏: 包含分段控制器 (Segmented Control) -->
     <header class="p-4 md:p-8 pb-2 md:pb-4 shrink-0">
       <h1 class="text-2xl md:text-3xl font-[900] text-text-main mb-4 md:mb-6 animate-slide-down-content">{{ t.navPickup }}</h1>
       
       <!-- Tab Switcher -->
       <div class="flex bg-white shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] p-1.5 md:p-2 rounded-full relative animate-scale-up w-full md:w-auto max-w-md mx-auto md:mx-0 border border-gray-100">
          <button 
             @click="activeTab = 'current'"
             class="flex-1 py-2 md:py-3 rounded-full text-xs md:text-sm font-black transition-all duration-500 ease-luxury relative z-10 active:scale-90 outline-none focus:outline-none"
             :class="activeTab === 'current' ? 'text-white' : 'text-gray-400'"
          >
             {{ t.currentOrders }}
          </button>
          <button 
             @click="activeTab = 'history'"
             class="flex-1 py-2 md:py-3 rounded-full text-xs md:text-sm font-black transition-all duration-500 ease-luxury relative z-10 active:scale-90 outline-none focus:outline-none"
             :class="activeTab === 'history' ? 'text-white' : 'text-gray-400'"
          >
             {{ t.pastOrders }}
          </button>
          
          <!-- Sliding Background Indicator (Pill) -->
          <!-- 动态滑块背景 -->
          <div 
            class="absolute top-1.5 bottom-1.5 md:top-2 md:bottom-2 rounded-full bg-primary shadow-lg shadow-primary/25 transition-all duration-500 ease-luxury z-0 w-[calc(50%_-_10px)] md:w-[calc(50%_-_12px)]"
            :class="activeTab === 'current' ? 'left-2 md:left-[10px]' : 'left-[calc(50%_+_2px)]'"
          ></div>
       </div>
     </header>

     <!-- Main Content List -->
     <main class="flex-1 overflow-y-auto p-4 md:p-8 pt-4 no-scrollbar scroll-smooth-touch pb-40">
        
        <!-- Tab 1: Current Orders -->
        <!-- 标签页 1: 当前订单 -->
        <div v-if="activeTab === 'current'" class="space-y-6">
           <!-- Empty State -->
           <div v-if="currentOrders.length === 0" class="flex flex-col items-center justify-center h-80 text-gray-400 animate-fade-in">
              <div class="bg-white p-8 rounded-full shadow-sm mb-6">
                <span class="material-symbols-rounded text-6xl opacity-30 text-primary">coffee_maker</span>
              </div>
              <p class="font-bold text-sm uppercase tracking-widest opacity-50">{{ t.noOrders }}</p>
           </div>
           
           <!-- Active Order Cards -->
           <div 
              v-else 
              v-for="(order, idx) in currentOrders" 
              :key="order.id" 
              class="bg-white rounded-[40px] p-8 shadow-[0_15px_40px_-5px_rgba(0,0,0,0.06)] transition-all duration-500 ease-luxury flex flex-col items-center text-center relative overflow-hidden animate-slide-up-content border border-gray-50 transform-gpu" 
              :style="{ animationDelay: `${idx * 100}ms` }"
           >
              <!-- Status Tag (Top Right) -->
              <div class="absolute top-4 right-4 md:top-6 md:right-6 bg-primary/5 text-primary px-4 py-1.5 rounded-full text-[10px] md:text-xs font-black uppercase tracking-wider flex items-center gap-2 shadow-inner border border-primary/10">
                 <span class="size-2 bg-primary rounded-full animate-pulse"></span>
                 {{ t.preparing }}
              </div>
              
              <!-- Time Stamp (Top Left) -->
              <div class="absolute top-4 left-4 md:top-6 md:left-6 text-gray-300 text-[10px] md:text-xs font-black tracking-widest font-mono">{{ formatTime(order.date) }}</div>

              <!-- Big Pickup Number Display -->
              <div class="text-gray-300 text-[10px] md:text-xs font-black uppercase tracking-[0.2em] mb-2 mt-4">{{ t.pickupNum }}</div>
              <div class="text-7xl md:text-9xl font-[900] text-primary tracking-tighter mb-4 scale-110 drop-shadow-sm animate-scale-up" :style="{ animationDelay: `${idx * 100 + 150}ms` }">{{ order.dailyNumber }}</div>
              
              
              <!-- UUID for verification (No QR) -->
              <div class="flex flex-col items-center mb-6 p-4 bg-white rounded-2xl shadow-sm border border-gray-100 w-full">
                  <p class="text-[10px] text-gray-400 font-black uppercase tracking-widest mb-1">ORDER ID</p>
                  <p class="text-xs font-mono text-text-main break-all max-w-[200px] leading-tight font-bold">{{ order.order_no }}</p>
              </div>

              <!-- Order Summary List -->
              <div class="w-full bg-background-light rounded-3xl p-5 mb-4 text-left space-y-3 shadow-inner">
                 <div v-for="(item, i) in order.items" :key="i" class="flex justify-between items-start text-xs md:text-sm">
                    <div class="flex items-start gap-3">
                       <span class="font-black text-primary whitespace-nowrap">{{ item.quantity }}x</span>
                       <div class="flex flex-col">
                           <span class="font-bold text-text-main text-base leading-none">
                              {{ lang === 'cn' ? item.nameCN : item.name }}
                           </span>

                       </div>
                    </div>
                 </div>
              </div>
              
              <!-- Footer Info -->
              <div class="flex items-center justify-between w-full px-4 text-[10px] md:text-xs text-text-main font-bold uppercase tracking-wider">
                 <span>{{ order.items.length }} {{ t.items }}</span>
                 <span class="font-mono bg-gray-50 px-2 py-0.5 rounded text-gray-400">#{{ order.id ? order.id.slice(0,6).toUpperCase() : '...' }}</span>
              </div>
           </div>
        </div>

        <!-- Tab 2: Past Orders -->
        <!-- 标签页 2: 历史订单 -->
        <div v-if="activeTab === 'history'" class="space-y-4">
           <!-- Empty State -->
           <div v-if="pastOrders.length === 0" class="flex flex-col items-center justify-center h-80 text-gray-400 animate-fade-in">
               <p class="font-bold opacity-50">{{ t.noOrders }}</p>
           </div>
           
           <!-- History Cards -->
           <div 
              v-else 
              v-for="(order, idx) in pastOrders" 
              :key="order.id" 
              class="bg-white p-6 rounded-[32px] flex flex-col gap-3 shadow-[0_4px_25px_rgba(0,0,0,0.03)] transition-all duration-500 ease-luxury active:scale-[0.96] animate-slide-up-content border border-gray-50"  
              :style="{ animationDelay: `${idx * 40}ms` }"
           >
              <!-- Order Header -->
              <div class="flex items-center justify-between">
                  <div class="flex items-center gap-4 md:gap-5">
                     <div class="size-12 md:size-14 bg-background-light rounded-2xl flex items-center justify-center font-black text-gray-500 text-lg transition-all duration-500">
                        {{ order.dailyNumber }}
                     </div>
                     <div>
                        <p class="font-black text-sm md:text-base text-text-main">{{ formatTime(order.date) }}</p>
                        <p class="text-[10px] md:text-xs text-gray-400 font-bold">{{ order.items.length }} {{ t.items }}</p>
                     </div>
                  </div>
                  <!-- Completion Tag -->
                  <div class="flex items-center gap-1 md:gap-2 text-green-700 bg-green-50 px-3 py-1.5 rounded-full text-[10px] md:text-xs font-black uppercase tracking-wide">
                     <span class="material-symbols-rounded text-sm">check_circle</span>
                     {{ t.completed }}
                  </div>
              </div>
              
              <!-- Items Summary -->
              <div class="text-[10px] md:text-xs text-text-sub border-t border-gray-100 pt-3 line-clamp-2 leading-relaxed font-medium">
                 {{ order.items.map(i => `${i.quantity}x ${lang === 'cn' ? i.nameCN : i.name}`).join(', ') }}
              </div>

               <!-- Mini UUID footer -->
               <div class="mt-2 pt-2 border-t border-dashed border-gray-100 flex items-center gap-2">
                   <p class="text-[9px] font-mono text-gray-300 truncate w-full">{{ order.order_no }}</p>
               </div>
           </div>
        </div>
     </main>
  </div>
</template>
