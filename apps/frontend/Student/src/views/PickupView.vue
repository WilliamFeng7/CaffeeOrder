<script setup lang="ts">
/**
 * PickupView.vue
 *
 * 取餐视图组件 (Pickup View Component).
 *
 * 主要功能 (Core Features):
 * 1. 订单分栏展示 (Tabbed Interface):
 *    - 当前订单 (Current): 展示 "active" 状态的订单 (排队 / 制作中 / 待取餐)。
 *    - 历史订单 (History): 展示 "completed" 状态的已完成订单。
 * 2. 状态可视化 (Visual Status): 大号取餐码，三段进度条随订单推进而生长。
 * 3. 实时更新 (Real-time Updates): 通过 props 接收最新的订单列表。
 */

import AppIcon from '@shared/components/AppIcon.vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
import { vReveal } from '@shared/reveal';
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
const activeTab = ref<'current' | 'history'>('current');

// 计算属性: 获取翻译
const t = computed(() => TRANSLATIONS[props.lang]);

const { scroller, onScroll } = useKeepScroll();

const tabOptions = computed(() => [
  { value: 'current' as const, label: t.value.currentOrders },
  { value: 'history' as const, label: t.value.pastOrders },
]);

// --- 计算属性 (Computed Properties) ---

/** 当前活跃订单: 状态为 'active' (排队、制作中、待取餐等非终态) */
const currentOrders = computed(() => props.orders.filter(o => o.status === 'active'));

/** 历史已完成订单: 状态为 'completed' */
const pastOrders = computed(() => props.orders.filter(o => o.status === 'completed'));

// --- 辅助方法 (Date Helpers) ---

/** 格式化时间字符串: YYYY/MM/DD HH:mm */
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
 * 进行中订单的阶段 (Stage): label + how far along the three-step bar is.
 * 排队中 / 制作中 / 请取餐 —— 以前所有进行中的订单都显示「制作中」，做好了也看不出来。
 */
const stageInfo = (order: Order): { label: string; step: number; progress: number } => {
  if (order.stage === 'ready') return { label: t.value.ready, step: 2, progress: 1 };
  if (order.stage === 'processing') return { label: t.value.preparing, step: 1, progress: 0.56 };
  return { label: t.value.queued, step: 0, progress: 0.14 };
};

const steps = computed(() => [t.value.queued, t.value.preparing, t.value.ready]);

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
     <header class="px-5 md:px-10 pt-6 md:pt-10 pb-5 shrink-0 max-w-3xl w-full mx-auto">
       <h1 class="font-serif text-[30px] md:text-[42px] font-medium leading-tight tracking-[-0.015em] text-text-main">{{ t.navPickup }}</h1>
       <SlidingTabs
         v-model="activeTab"
         :options="tabOptions"
         variant="segment"
         size="lg"
         stretch
         :label="t.navPickup"
         class="mt-5 w-full md:max-w-sm"
       />
     </header>

     <!-- Lists (swipe left/right to switch) -->
     <main ref="scroller" @scroll.passive="onScroll" class="flex-1 overflow-y-auto overflow-x-hidden no-scrollbar scroll-smooth-touch pb-40 touch-pan-y" @pointerdown="onSwipeStart" @pointerup="onSwipeEnd" @pointercancel="onSwipeEnd">
        <div class="px-5 md:px-10 pt-2 max-w-3xl mx-auto">
        <Transition :name="activeTab === 'history' ? 'grid-next' : 'grid-prev'" mode="out-in">

        <!-- Current Orders -->
        <div v-if="activeTab === 'current'" key="current">
           <div v-if="currentOrders.length === 0" class="py-24 flex flex-col items-center text-text-sub animate-fade-in">
              <AppIcon name="coffee" weight="light" class="text-3xl mb-3" />
              <p class="text-[15px]">{{ t.noOrders }}</p>
           </div>

           <TransitionGroup v-else tag="div" name="list" class="relative space-y-4">
              <article
                 v-for="(order, idx) in currentOrders"
                 :key="order.id"
                 class="card p-6 md:p-7 animate-slide-up-content transition-colors duration-fade"
                 :class="order.stage === 'ready' ? '!border-primary/40' : ''"
                 :style="{ animationDelay: `${Math.min(idx, 6) * 60}ms` }"
              >
                 <div class="flex items-start justify-between gap-3">
                    <div>
                       <p class="eyebrow">{{ t.pickupNum }}</p>
                       <p class="mt-2 font-serif text-[60px] md:text-[72px] font-medium leading-[0.9] tabular-nums animate-text-reveal transition-colors duration-fade" :class="order.stage === 'ready' ? 'text-primary' : 'text-text-main'" style="animation-delay: 120ms">{{ order.dailyNumber }}</p>
                    </div>
                    <!-- Stage: a dot that pings once when the order moves on -->
                    <span class="flex items-center gap-2 text-[13px] font-medium pt-1" :class="order.stage === 'ready' ? 'text-primary' : 'text-text-main'">
                       <span class="relative flex size-2">
                          <span :key="order.stage" class="absolute inset-0 rounded-full ping" :class="order.stage === 'ready' ? 'bg-primary' : 'bg-text-sub'" aria-hidden="true"></span>
                          <!-- while it waits at the counter, a slow halo keeps it noticeable -->
                          <span v-if="order.stage === 'ready'" class="absolute inset-0 rounded-full bg-primary breathe" style="animation-delay: 1.1s" aria-hidden="true"></span>
                          <span
                             class="relative size-2 rounded-full"
                             :class="order.stage === 'ready' ? 'bg-primary' : order.stage === 'processing' ? 'bg-text-main animate-pulse' : 'bg-text-sub'"
                             aria-hidden="true"
                          ></span>
                       </span>
                       <span class="grid overflow-hidden">
                          <Transition name="roll-up">
                             <span :key="order.stage" class="col-start-1 row-start-1">{{ stageInfo(order).label }}</span>
                          </Transition>
                       </span>
                    </span>
                 </div>

                 <!-- Three-step progress: the bar grows as the order moves on -->
                 <div class="mt-7" role="progressbar" aria-valuemin="1" aria-valuemax="3" :aria-valuenow="stageInfo(order).step + 1" :aria-valuetext="stageInfo(order).label">
                    <div class="relative h-[3px] rounded-full bg-line overflow-hidden">
                       <div
                          class="absolute inset-0 origin-left rounded-full bg-primary grow-x transition-transform duration-spring-soft ease-spring-soft"
                          :style="{ transform: `scaleX(${stageInfo(order).progress})` }"
                       ></div>
                    </div>
                    <div class="mt-2.5 grid grid-cols-3 text-[12px]">
                       <span
                          v-for="(label, s) in steps"
                          :key="s"
                          class="transition-colors duration-fade"
                          :class="[
                            s === 0 ? 'text-left' : s === 1 ? 'text-center' : 'text-right',
                            s <= stageInfo(order).step ? 'text-text-main font-medium' : 'text-text-sub',
                          ]"
                       >{{ label }}</span>
                    </div>
                 </div>

                 <div class="mt-6 border-t border-line pt-4 space-y-2">
                    <div v-for="(item, i) in order.items" :key="i" class="flex items-baseline gap-2.5 text-[15px]">
                       <span class="text-text-sub tabular-nums">{{ item.quantity }}×</span>
                       <span class="text-text-main min-w-0 truncate">{{ lang === 'cn' ? item.nameCN : item.name }}</span>
                       <span v-if="specLine(item)" class="ml-auto text-[13px] text-text-sub whitespace-nowrap">{{ specLine(item) }}</span>
                    </div>
                 </div>

                 <div class="flex items-end justify-between gap-4 mt-5 text-[12px] text-text-sub">
                    <span class="tabular-nums leading-relaxed">
                       {{ formatTime(order.date) }} · {{ itemCount(order) }}
                       <span class="block font-mono text-[11px] text-text-sub/80">{{ order.order_no }}</span>
                    </span>
                    <span class="font-serif text-[20px] font-medium text-text-main tabular-nums">¥{{ order.total.toFixed(2) }}</span>
                 </div>
              </article>
           </TransitionGroup>
        </div>

        <!-- Past Orders: a hairline list that reveals as it scrolls -->
        <div v-else key="history">
           <div v-if="pastOrders.length === 0" class="py-24 flex flex-col items-center text-text-sub animate-fade-in">
              <AppIcon name="receipt" weight="light" class="text-3xl mb-3" />
              <p class="text-[15px]">{{ t.noOrders }}</p>
           </div>

           <ul v-else class="border-y border-line divide-y divide-line">
              <li
                 v-for="(order, idx) in pastOrders"
                 :key="order.id"
                 v-reveal="Math.min(idx, 8) * 40"
                 class="py-4 flex flex-col gap-1.5"
              >
                 <div class="flex items-center justify-between gap-3">
                     <div class="flex items-center gap-4 min-w-0">
                        <span class="w-12 font-serif text-[26px] font-medium text-text-main tabular-nums leading-none">{{ order.dailyNumber }}</span>
                        <div class="min-w-0">
                           <p class="text-[15px] text-text-main tabular-nums">{{ formatTime(order.date) }}</p>
                           <p class="text-[13px] text-text-sub tabular-nums">{{ itemCount(order) }} · ¥{{ order.total.toFixed(2) }}</p>
                        </div>
                     </div>
                     <span class="flex items-center gap-1.5 text-[12px] font-medium shrink-0" :class="order.stage === 'refunded' ? 'text-text-sub' : 'text-primary'">
                        <span class="dot" aria-hidden="true"></span>
                        {{ order.stage === 'refunded' ? (lang === 'cn' ? '已退款' : 'Refunded') : t.completed }}
                     </span>
                 </div>
                 <p class="pl-16 text-[13px] text-text-sub line-clamp-1">
                    {{ order.items.map(i => `${i.quantity}× ${lang === 'cn' ? i.nameCN : i.name}`).join('，') }}
                 </p>
              </li>
           </ul>
        </div>
        </Transition>
        </div>
     </main>
  </div>
</template>
