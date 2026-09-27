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

import AppIcon from '@shared/components/AppIcon.vue';
import { ref, computed } from 'vue';
import { TRANSLATIONS, OPTION_TRANSLATIONS } from '../data';
import type { Order, Language } from '../types';
import { useKeepScroll } from '../composables/useKeepScroll';
import type { IconName } from '@shared/icons';

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
const stageChip = (order: Order): { label: string; icon: IconName | null; cls: string } => {
  if (order.stage === 'ready') {
    return { label: t.value.ready, icon: 'bell', cls: 'bg-secondary-soft text-secondary-content' };
  }
  if (order.stage === 'processing') {
    return { label: t.value.preparing, icon: null, cls: 'bg-primary-soft text-primary' };
  }
  return { label: t.value.queued, icon: 'clock', cls: 'bg-cream text-text-main' };
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
  <div class="flex flex-col h-full bg-background-light">
     <!-- Title + segmented control -->
     <header class="px-5 md:px-10 pt-6 md:pt-10 pb-4 shrink-0 max-w-3xl w-full mx-auto">
       <h1 class="font-serif text-[30px] md:text-[40px] font-medium leading-tight tracking-[-0.01em] text-text-main">{{ t.navPickup }}</h1>

       <div class="relative mt-5 flex bg-cream p-1 rounded-full w-full md:max-w-sm">
          <!-- Sliding thumb (springs; transform only) -->
          <div
            class="absolute top-1 bottom-1 left-1 w-[calc(50%-4px)] rounded-full bg-surface-light shadow-card transition-transform duration-spring ease-spring"
            :class="activeTab === 'current' ? 'translate-x-0' : 'translate-x-full'"
            aria-hidden="true"
          ></div>
          <button
             type="button"
             @click="activeTab = 'current'"
             :aria-pressed="activeTab === 'current'"
             class="relative z-10 flex-1 min-h-10 rounded-full text-[14px] transition-colors duration-color"
             :class="activeTab === 'current' ? 'text-text-main font-medium' : 'text-text-sub'"
          >
             {{ t.currentOrders }}
          </button>
          <button
             type="button"
             @click="activeTab = 'history'"
             :aria-pressed="activeTab === 'history'"
             class="relative z-10 flex-1 min-h-10 rounded-full text-[14px] transition-colors duration-color"
             :class="activeTab === 'history' ? 'text-text-main font-medium' : 'text-text-sub'"
          >
             {{ t.pastOrders }}
          </button>
       </div>
     </header>

     <!-- Lists (swipe left/right to switch) -->
     <main ref="scroller" @scroll.passive="onScroll" class="flex-1 overflow-y-auto no-scrollbar scroll-smooth-touch pb-40 touch-pan-y" @pointerdown="onSwipeStart" @pointerup="onSwipeEnd" @pointercancel="onSwipeEnd">
        <div class="px-5 md:px-10 pt-2 max-w-3xl mx-auto">

        <!-- Current Orders -->
        <div v-if="activeTab === 'current'" class="space-y-4">
           <div v-if="currentOrders.length === 0" class="py-24 flex flex-col items-center text-text-sub animate-fade-in">
              <AppIcon name="coffee" class="text-3xl mb-3" />
              <p class="text-[15px]">{{ t.noOrders }}</p>
           </div>

           <article
              v-else
              v-for="(order, idx) in currentOrders"
              :key="order.id"
              class="bg-surface-light rounded-card border p-5 md:p-6 animate-slide-up-content transition-colors duration-fade"
              :class="order.stage === 'ready' ? 'border-secondary' : 'border-line'"
              :style="{ animationDelay: `${Math.min(idx, 6) * 45}ms` }"
           >
              <div class="flex items-start justify-between gap-3">
                 <div>
                    <p class="text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub">{{ t.pickupNum }}</p>
                    <p class="mt-1 font-serif text-[48px] md:text-[56px] font-medium text-primary leading-none tabular-nums">{{ order.dailyNumber }}</p>
                 </div>
                 <!-- Keyed by stage so the chip pops once when the order moves on -->
                 <span :key="order.stage" class="h-8 px-3 rounded-full text-[13px] font-medium flex items-center gap-1.5 shrink-0 animate-scale-in" :class="stageChip(order).cls">
                    <AppIcon v-if="stageChip(order).icon" :name="stageChip(order).icon!" weight="fill" class="text-base" />
                    <span v-else class="size-2 bg-primary rounded-full animate-pulse" aria-hidden="true"></span>
                    {{ stageChip(order).label }}
                 </span>
              </div>

              <p class="mt-4 text-[12px] text-text-sub tabular-nums">
                 {{ formatTime(order.date) }}
                 <span class="mx-1" aria-hidden="true">·</span>
                 <span class="font-mono">{{ order.order_no }}</span>
              </p>

              <div class="mt-4 border-t border-line pt-4 space-y-2">
                 <div v-for="(item, i) in order.items" :key="i" class="flex items-baseline gap-2.5 text-[15px]">
                    <span class="text-text-sub tabular-nums">{{ item.quantity }}×</span>
                    <span class="text-text-main min-w-0 truncate">{{ lang === 'cn' ? item.nameCN : item.name }}</span>
                    <span v-if="specLine(item)" class="ml-auto text-[13px] text-text-sub whitespace-nowrap">{{ specLine(item) }}</span>
                 </div>
              </div>

              <div class="flex items-center justify-between mt-4 text-[13px] text-text-sub">
                 <span>{{ itemCount(order) }}</span>
                 <span class="text-[16px] font-medium text-text-main tabular-nums">¥{{ order.total.toFixed(2) }}</span>
              </div>
           </article>
        </div>

        <!-- Past Orders: a hairline list -->
        <div v-if="activeTab === 'history'">
           <div v-if="pastOrders.length === 0" class="py-24 flex flex-col items-center text-text-sub animate-fade-in">
              <AppIcon name="receipt" class="text-3xl mb-3" />
              <p class="text-[15px]">{{ t.noOrders }}</p>
           </div>

           <ul v-else class="divide-y divide-line border-y border-line">
              <li
                 v-for="(order, idx) in pastOrders"
                 :key="order.id"
                 class="py-4 flex flex-col gap-2 animate-slide-up-content"
                 :style="{ animationDelay: `${Math.min(idx, 8) * 40}ms` }"
              >
                 <div class="flex items-center justify-between gap-3">
                     <div class="flex items-center gap-4 min-w-0">
                        <span class="w-12 font-serif text-[26px] font-medium text-text-main tabular-nums leading-none">{{ order.dailyNumber }}</span>
                        <div class="min-w-0">
                           <p class="text-[15px] text-text-main tabular-nums">{{ formatTime(order.date) }}</p>
                           <p class="text-[13px] text-text-sub tabular-nums">{{ itemCount(order) }} · ¥{{ order.total.toFixed(2) }}</p>
                        </div>
                     </div>
                     <span v-if="order.stage === 'refunded'" class="h-7 px-2.5 rounded-full bg-cream text-text-sub text-[12px] font-medium flex items-center gap-1 shrink-0">
                        <AppIcon name="undo" class="text-sm" />
                        {{ lang === 'cn' ? '已退款' : 'Refunded' }}
                     </span>
                     <span v-else class="h-7 px-2.5 rounded-full bg-primary-soft text-primary text-[12px] font-medium flex items-center gap-1 shrink-0">
                        <AppIcon name="check" class="text-sm" />
                        {{ t.completed }}
                     </span>
                 </div>
                 <p class="pl-16 text-[13px] text-text-sub line-clamp-1">
                    {{ order.items.map(i => `${i.quantity}× ${lang === 'cn' ? i.nameCN : i.name}`).join('，') }}
                 </p>
              </li>
           </ul>
        </div>
        </div>
     </main>
  </div>
</template>
