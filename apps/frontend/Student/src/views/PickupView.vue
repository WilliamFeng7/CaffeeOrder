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
import { TRANSLATIONS, OPTION_TRANSLATIONS } from '../data';
import type { Order, Language } from '../types';
import { useKeepScroll } from '../composables/useKeepScroll';

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

const { scroller, onScroll } = useKeepScroll();

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

/**
 * 进行中订单的阶段标签 (Stage chip)
 * 排队中 / 制作中 / 请取餐 —— 以前所有进行中的订单都显示「制作中」，做好了也看不出来。
 */
const stageChip = (order: Order) => {
  if (order.stage === 'ready') {
    return { label: t.value.ready, icon: 'notifications_active', cls: 'bg-[#DCCA98] text-[#2C2108] border-[#DCCA98]' };
  }
  if (order.stage === 'processing') {
    return { label: t.value.preparing, icon: '', cls: 'bg-primary/5 text-primary border-primary/10' };
  }
  return { label: t.value.queued, icon: 'schedule', cls: 'bg-gray-50 text-text-sub border-gray-100' };
};

/**
 * 左右滑动切换「当前订单 / 历史订单」(Swipe between the two tabs)
 * The list is `touch-pan-y`: a vertical drag scrolls as usual (the browser
 * cancels the pointer), a clearly horizontal one switches the tab.
 */
let swipe: { id: number; x: number; y: number } | null = null;
const onSwipeStart = (e: PointerEvent) => {
  if (e.pointerType === 'mouse' || swipe) return;
  swipe = { id: e.pointerId, x: e.clientX, y: e.clientY };
};
const onSwipeEnd = (e: PointerEvent) => {
  if (!swipe || e.pointerId !== swipe.id) return;
  const dx = e.clientX - swipe.x;
  const dy = e.clientY - swipe.y;
  swipe = null;
  if (e.type !== 'pointerup' || Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
  activeTab.value = dx < 0 ? 'history' : 'current';
};

const itemCount = (order: Order) => {
  const n = order.items.reduce((sum, item) => sum + item.quantity, 0);
  if (props.lang === 'cn') return `${n} 件`;
  return `${n} ${n === 1 ? 'item' : 'items'}`;
};

const specLine = (item: Order['items'][number]) => {
  const temp = item.temperature ? (item.temperature === 'Hot' ? t.value.hot : t.value.iced) : '';
  const sugarLabels = OPTION_TRANSLATIONS.sugar as Record<string, { en: string; cn: string }>;
  const sugar = item.sugar ? (sugarLabels[item.sugar]?.[props.lang] ?? item.sugar) : '';
  return [temp, sugar].filter(Boolean).join(' · ');
};

</script>

<template>
  <div class="flex flex-col h-full bg-background-light animate-fade-in">
     <!-- Top Header with Segmented Control -->
     <!-- 顶部导航栏: 包含分段控制器 (Segmented Control) -->
     <header class="px-4 pt-6 pb-2 md:px-8 md:pt-8 md:pb-4 shrink-0 max-w-3xl w-full mx-auto">
       <h1 class="text-2xl md:text-3xl font-[900] text-text-main mb-4 md:mb-5 animate-slide-down-content">{{ t.navPickup }}</h1>
       
       <!-- Tab Switcher -->
       <div class="flex bg-white shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] p-1.5 rounded-full relative w-full md:max-w-md border border-gray-100">
          <button 
             type="button"
             @click="activeTab = 'current'"
             :aria-pressed="activeTab === 'current'"
             class="flex-1 min-h-11 py-2.5 md:py-3 rounded-full text-xs md:text-sm font-black transition-colors duration-200 relative z-10 outline-none focus:outline-none"
             :class="activeTab === 'current' ? 'text-white' : 'text-text-sub'"
          >
             {{ t.currentOrders }}
          </button>
          <button 
             type="button"
             @click="activeTab = 'history'"
             :aria-pressed="activeTab === 'history'"
             class="flex-1 min-h-11 py-2.5 md:py-3 rounded-full text-xs md:text-sm font-black transition-colors duration-200 relative z-10 outline-none focus:outline-none"
             :class="activeTab === 'history' ? 'text-white' : 'text-text-sub'"
          >
             {{ t.pastOrders }}
          </button>
          
          <!-- Sliding Background Indicator (Pill): moved with transform, not `left` -->
          <!-- 动态滑块背景 -->
          <div 
            class="absolute top-1.5 bottom-1.5 left-1.5 w-[calc(50%_-_6px)] rounded-full bg-primary shadow-lg shadow-primary/25 transition-transform duration-300 ease-out z-0"
            :class="activeTab === 'current' ? 'translate-x-0' : 'translate-x-full'"
            aria-hidden="true"
          ></div>
       </div>
     </header>

     <!-- Main Content List -->
     <main ref="scroller" @scroll.passive="onScroll" class="flex-1 overflow-y-auto no-scrollbar scroll-smooth-touch pb-40 touch-pan-y" @pointerdown="onSwipeStart" @pointerup="onSwipeEnd" @pointercancel="onSwipeEnd">
        <div class="px-4 md:px-8 pt-3 max-w-3xl mx-auto">
        
        <!-- Tab 1: Current Orders -->
        <!-- 标签页 1: 当前订单 -->
        <div v-if="activeTab === 'current'" class="space-y-4">
           <!-- Empty State -->
           <div v-if="currentOrders.length === 0" class="flex flex-col items-center justify-center h-72 text-text-sub animate-fade-in">
              <div class="bg-white p-7 rounded-full shadow-sm mb-5">
                <span class="material-symbols-rounded text-5xl opacity-40 text-primary" aria-hidden="true">coffee_maker</span>
              </div>
              <p class="font-bold text-sm uppercase tracking-widest">{{ t.noOrders }}</p>
           </div>
           
           <!-- Active Order Cards -->
           <div 
              v-else 
              v-for="(order, idx) in currentOrders" 
              :key="order.id" 
              class="bg-white rounded-[28px] p-5 md:p-6 shadow-[0_15px_40px_-5px_rgba(0,0,0,0.06)] border relative overflow-hidden animate-slide-up-content transition-[box-shadow,border-color] duration-300" 
              :class="order.stage === 'ready' ? 'border-[#DCCA98] ring-2 ring-[#DCCA98]/60' : 'border-gray-50'"
              :style="{ animationDelay: `${Math.min(idx, 6) * 40}ms` }"
           >
              <!-- Pickup Number + Stage -->
              <div class="flex items-start justify-between gap-3">
                 <div>
                    <div class="text-text-sub text-[10px] md:text-xs font-black uppercase tracking-[0.2em]">{{ t.pickupNum }}</div>
                    <div class="text-6xl md:text-7xl font-[900] text-primary tracking-tighter leading-none mt-1.5 tabular-nums">{{ order.dailyNumber }}</div>
                 </div>
                 <!-- Keyed by stage so the chip pops once when the order moves on -->
                 <div :key="order.stage" class="px-3.5 py-1.5 rounded-full text-[11px] md:text-xs font-black uppercase tracking-wider flex items-center gap-1.5 border shrink-0 animate-scale-in" :class="stageChip(order).cls">
                    <span v-if="stageChip(order).icon" class="material-symbols-rounded text-base filled" aria-hidden="true">{{ stageChip(order).icon }}</span>
                    <span v-else class="size-2 bg-primary rounded-full animate-pulse" aria-hidden="true"></span>
                    {{ stageChip(order).label }}
                 </div>
              </div>

              <!-- Time + order number for the counter -->
              <p class="mt-3 text-[11px] md:text-xs text-text-sub font-bold tracking-wide">
                 {{ formatTime(order.date) }}
                 <span class="mx-1.5 text-gray-300" aria-hidden="true">·</span>
                 <span class="font-mono">{{ order.order_no }}</span>
              </p>

              <!-- Order Summary List -->
              <div class="mt-4 bg-background-light rounded-2xl px-4 py-3 space-y-2.5">
                 <div v-for="(item, i) in order.items" :key="i" class="flex items-baseline gap-3 text-sm">
                    <span class="font-black text-primary whitespace-nowrap tabular-nums">{{ item.quantity }}×</span>
                    <span class="font-bold text-text-main min-w-0 truncate">{{ lang === 'cn' ? item.nameCN : item.name }}</span>
                    <span v-if="specLine(item)" class="ml-auto text-[11px] font-bold text-text-sub whitespace-nowrap">{{ specLine(item) }}</span>
                 </div>
              </div>
              
              <!-- Footer Info -->
              <div class="flex items-center justify-between mt-3 px-1 text-xs font-bold text-text-sub">
                 <span>{{ itemCount(order) }}</span>
                 <span class="text-text-main font-black tabular-nums">¥{{ order.total.toFixed(2) }}</span>
              </div>
           </div>
        </div>

        <!-- Tab 2: Past Orders -->
        <!-- 标签页 2: 历史订单 -->
        <div v-if="activeTab === 'history'" class="space-y-3">
           <!-- Empty State -->
           <div v-if="pastOrders.length === 0" class="flex flex-col items-center justify-center h-72 text-text-sub animate-fade-in">
               <p class="font-bold">{{ t.noOrders }}</p>
           </div>
           
           <!-- History Cards -->
           <div 
              v-else 
              v-for="(order, idx) in pastOrders" 
              :key="order.id" 
              class="bg-white p-5 rounded-[24px] flex flex-col gap-3 shadow-[0_4px_25px_rgba(0,0,0,0.03)] animate-slide-up-content border border-gray-50"  
              :style="{ animationDelay: `${Math.min(idx, 8) * 30}ms` }"
           >
              <!-- Order Header -->
              <div class="flex items-center justify-between gap-3">
                  <div class="flex items-center gap-4 min-w-0">
                     <div class="size-12 bg-background-light rounded-2xl flex items-center justify-center font-black text-text-sub text-lg shrink-0 tabular-nums">
                        {{ order.dailyNumber }}
                     </div>
                     <div class="min-w-0">
                        <p class="font-black text-sm md:text-base text-text-main">{{ formatTime(order.date) }}</p>
                        <p class="text-[11px] md:text-xs text-text-sub font-bold">{{ itemCount(order) }} · ¥{{ order.total.toFixed(2) }}</p>
                     </div>
                  </div>
                  <!-- Completion Tag -->
                  <div v-if="order.stage === 'refunded'" class="flex items-center gap-1 text-text-sub bg-gray-100 px-3 py-1.5 rounded-full text-[10px] md:text-xs font-black uppercase tracking-wide shrink-0">
                     <span class="material-symbols-rounded text-sm" aria-hidden="true">undo</span>
                     {{ lang === 'cn' ? '已退款' : 'Refunded' }}
                  </div>
                  <div v-else class="flex items-center gap-1 text-green-700 bg-green-50 px-3 py-1.5 rounded-full text-[10px] md:text-xs font-black uppercase tracking-wide shrink-0">
                     <span class="material-symbols-rounded text-sm" aria-hidden="true">check_circle</span>
                     {{ t.completed }}
                  </div>
              </div>
              
              <!-- Items Summary -->
              <div class="text-xs text-text-sub border-t border-gray-100 pt-3 line-clamp-2 leading-relaxed font-medium">
                 {{ order.items.map(i => `${i.quantity}x ${lang === 'cn' ? i.nameCN : i.name}`).join(', ') }}
              </div>

               <!-- Mini order number footer -->
               <p class="text-[10px] font-mono text-gray-400 truncate">{{ order.order_no }}</p>
           </div>
        </div>
        </div>
     </main>
  </div>
</template>
