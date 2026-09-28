<script setup lang="ts">
/**
 * PickupView.vue
 *
 * 取餐视图组件 (Pickup View Component).
 *
 * 主要功能 (Core Features):
 * 1. 当前订单 / 历史订单两页 (two pages side by side).
 * 2. 状态可视化 (Visual Status): 大号取餐码，三段进度条随订单推进而生长。
 * 3. 实时更新 (Real-time Updates): 通过 props 接收最新的订单列表；下拉可立即刷新。
 *
 * Touch: the pages follow the finger sideways (rubber band past the ends),
 * and on release a spring carries the finger's velocity to the page the
 * flick was heading for; the segmented control's thumb tracks the pages the
 * whole way. Pulling a list down at its top refreshes it.
 */

import AppIcon from '@/components/AppIcon.vue';
import { vReveal } from '@shared/reveal';
import { ref, computed, onMounted, onBeforeUnmount, onActivated } from 'vue';
import { TRANSLATIONS, OPTION_TRANSLATIONS } from '../data';
import type { Order, Language } from '../types';
import { useKeepScroll } from '../composables/useKeepScroll';
import { usePullToRefresh } from '../composables/usePullToRefresh';
import { spring, project, rubberband, VelocityTracker, type SpringHandle } from '../composables/spring';

// --- Props & Events ---
const props = defineProps<{
  orders: Order[]; // 全量订单列表数据源
  lang: Language;  // 当前语言
  /** Fetch the orders now (pull to refresh). */
  refresh?: () => Promise<unknown>;
}>();

// 计算属性: 获取翻译
const t = computed(() => TRANSLATIONS[props.lang]);

// --- 两页 (the two pages) ------------------------------------------------------
// 0 = current orders, 1 = past orders. The track and the thumb are moved by
// writing their transform directly, so a drag never re-renders the lists.
const page = ref(0);
const viewport = ref<HTMLElement | null>(null);
const track = ref<HTMLElement | null>(null);
const thumb = ref<HTMLElement | null>(null);
let width = 0;
let offset = 0;
let anim: SpringHandle | null = null;

const paint = (x: number) => {
  offset = x;
  if (track.value) track.value.style.transform = `translate3d(${x}px, 0, 0)`;
  const progress = width ? -x / width : page.value;
  if (thumb.value) thumb.value.style.transform = `translate3d(${progress * 100}%, 0, 0)`;
};

const goTo = (index: number, velocity = 0) => {
  page.value = index;
  anim?.stop();
  // A flick lands with a touch of bounce; a tap settles without one.
  anim = spring(offset, -index * width, {
    response: 0.42,
    dampingRatio: Math.abs(velocity) > 300 ? 0.86 : 1,
    velocity,
    onUpdate: paint,
  });
};

const measure = () => {
  if (!viewport.value) return;
  width = viewport.value.clientWidth;
  anim?.stop();
  paint(-page.value * width);
};

let resizeObserver: ResizeObserver | null = null;
onMounted(() => {
  measure();
  if (typeof ResizeObserver !== 'undefined' && viewport.value) {
    resizeObserver = new ResizeObserver(measure);
    resizeObserver.observe(viewport.value);
  }
});
onActivated(measure);
onBeforeUnmount(() => {
  anim?.stop();
  resizeObserver?.disconnect();
});

// Sideways drag: decided after 10px, then 1:1 with the finger.
const velocity = new VelocityTracker();
let drag: { id: number; x: number; y: number; start: number; horizontal: boolean | null } | null = null;

const onPointerDown = (e: PointerEvent) => {
  if (e.pointerType === 'mouse' || drag) return;
  drag = { id: e.pointerId, x: e.clientX, y: e.clientY, start: offset, horizontal: null };
  velocity.reset();
};

const onPointerMove = (e: PointerEvent) => {
  if (!drag || e.pointerId !== drag.id) return;
  const dx = e.clientX - drag.x;
  const dy = e.clientY - drag.y;
  if (drag.horizontal === null) {
    if (Math.abs(dx) < 10 && Math.abs(dy) < 10) return;
    drag.horizontal = Math.abs(dx) > Math.abs(dy) * 1.2;
    if (!drag.horizontal) {
      drag = null; // a vertical scroll: the browser has it
      return;
    }
    anim?.stop();
    drag.start = offset;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }
  let x = drag.start + dx;
  if (x > 0) x = rubberband(x, width);
  else if (x < -width) x = -width - rubberband(-width - x, width);
  velocity.push(x);
  paint(x);
};

const onPointerEnd = (e: PointerEvent) => {
  if (!drag || e.pointerId !== drag.id) return;
  const horizontal = drag.horizontal;
  drag = null;
  if (!horizontal) return;
  // Aim for where the flick is heading, not where the finger let go.
  const v = velocity.velocity;
  const landing = offset + project(v);
  goTo(landing < -width / 2 ? 1 : 0, v);
};

// --- 列表 (lists) ------------------------------------------------------------
const currentScroll = useKeepScroll();
const historyScroll = useKeepScroll();
const currentContent = ref<HTMLElement | null>(null);
const historyContent = ref<HTMLElement | null>(null);
const currentIndicator = ref<HTMLElement | null>(null);
const historyIndicator = ref<HTMLElement | null>(null);
const doRefresh = () => props.refresh?.() ?? Promise.resolve();
const { refreshing: refreshingCurrent } = usePullToRefresh(currentScroll.scroller, currentContent, currentIndicator, doRefresh);
const { refreshing: refreshingHistory } = usePullToRefresh(historyScroll.scroller, historyContent, historyIndicator, doRefresh);
const setCurrentScroller = (el: unknown) => { currentScroll.scroller.value = el as HTMLElement | null; };
const setHistoryScroller = (el: unknown) => { historyScroll.scroller.value = el as HTMLElement | null; };

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
     <!-- Title + segmented control (its thumb follows the pages) -->
     <header class="px-5 md:px-10 pt-6 md:pt-10 pb-5 shrink-0 max-w-3xl w-full mx-auto">
       <h1 class="font-serif text-[30px] md:text-[42px] font-medium leading-tight tracking-[-0.015em] text-text-main">{{ t.navPickup }}</h1>
       <div class="relative mt-5 grid grid-cols-2 p-1 rounded-full bg-cream w-full md:max-w-sm" role="tablist" :aria-label="t.navPickup">
          <span ref="thumb" class="absolute top-1 bottom-1 left-1 w-[calc(50%-4px)] rounded-full bg-surface-light shadow-card pointer-events-none" aria-hidden="true"></span>
          <button
             v-for="(label, i) in [t.currentOrders, t.pastOrders]"
             :key="i"
             type="button"
             role="tab"
             :aria-selected="page === i"
             class="relative z-10 h-11 rounded-full text-[15px] transition-colors duration-color"
             :class="page === i ? 'text-text-main font-medium' : 'text-text-sub'"
             @click="goTo(i)"
          >{{ label }}</button>
       </div>
     </header>

     <!-- Two pages side by side; swipe sideways between them -->
     <main
        ref="viewport"
        class="relative flex-1 overflow-hidden touch-pan-y"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerEnd"
        @pointercancel="onPointerEnd"
     >
        <div ref="track" class="flex h-full w-[200%] will-change-transform">

        <!-- Current Orders -->
        <section :ref="setCurrentScroller" @scroll.passive="currentScroll.onScroll" class="relative w-1/2 h-full overflow-y-auto overflow-x-hidden no-scrollbar overscroll-contain" :aria-hidden="page !== 0">
           <div ref="currentIndicator" class="ptr absolute left-1/2 top-0 z-10 size-7 text-text-sub" :class="{ 'is-refreshing': refreshingCurrent }" style="opacity: 0" aria-hidden="true">
              <svg viewBox="0 0 24 24" class="size-full" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="8.5" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" /></svg>
           </div>
           <div ref="currentContent" class="px-5 md:px-10 pt-2 pb-40 max-w-3xl mx-auto">
           <div v-if="currentOrders.length === 0" class="py-24 flex flex-col items-center text-text-sub animate-fade-in">
              <AppIcon name="coffee" weight="light" draw class="text-[34px] mb-3" />
              <p class="text-[15px]">{{ t.noOrders }}</p>
           </div>

           <TransitionGroup v-else tag="div" name="list" class="relative space-y-4">
              <article
                 v-for="(order, idx) in currentOrders"
                 :key="order.id"
                 class="card p-6 md:p-7 animate-slide-up-content transition-colors duration-fade"
                 :class="order.stage === 'ready' ? '!border-primary/40 ready-lift' : ''"
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
        </section>

        <!-- Past Orders: a hairline list that reveals as it scrolls -->
        <section :ref="setHistoryScroller" @scroll.passive="historyScroll.onScroll" class="relative w-1/2 h-full overflow-y-auto overflow-x-hidden no-scrollbar overscroll-contain" :aria-hidden="page !== 1">
           <div ref="historyIndicator" class="ptr absolute left-1/2 top-0 z-10 size-7 text-text-sub" :class="{ 'is-refreshing': refreshingHistory }" style="opacity: 0" aria-hidden="true">
              <svg viewBox="0 0 24 24" class="size-full" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="8.5" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" /></svg>
           </div>
           <div ref="historyContent" class="px-5 md:px-10 pt-2 pb-40 max-w-3xl mx-auto">
           <div v-if="pastOrders.length === 0" class="py-24 flex flex-col items-center text-text-sub animate-fade-in">
              <AppIcon name="receipt" weight="light" draw class="text-[34px] mb-3" />
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
        </section>
        </div>
     </main>
  </div>
</template>

<style scoped>
/* Pull-to-refresh ring: closes as you pull, then turns while it loads. */
.ptr.is-refreshing svg {
  animation: ptrSpin 0.9s linear infinite;
}

.ptr.is-refreshing circle {
  stroke-dashoffset: 0.72 !important;
}

@keyframes ptrSpin {
  to {
    transform: rotate(360deg);
  }
}
</style>
