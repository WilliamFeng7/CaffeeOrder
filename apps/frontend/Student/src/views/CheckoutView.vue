<script setup lang="ts">
/**
 * CheckoutView.vue
 * 
 * 结算页面视图组件 (Checkout View Component).
 * 
 * 主要功能 (Core Features):
 * 1. 购物车商品展示 (Cart Review): 显示所选商品详情(规格、糖度等)。
 * 2. 数量管理 (Quantity Control): 增减商品数量。
 * 3. 价格计算 (Price Calculation): 实时计算小计和总价。
 * 4. 支付 (Payment): 模拟支付流程，提交订单。
 */

import AppIcon from '@shared/components/AppIcon.vue';
import { computed, ref } from 'vue';
import { TRANSLATIONS } from '../data';
import { formatCents, toCents, sumCents } from '../utils/money';
import type { CartItem, ViewState, Language } from '../types';
import { useSheetDrag } from '../composables/useSheetDrag';

// --- Props & Events ---
const props = defineProps<{
  cart: CartItem[]; // 购物车数据源
  lang: Language;   // 当前语言
  placing?: boolean; // 下单请求进行中 (按钮禁用，防止重复扣款)
}>();

const emit = defineEmits<{
  (e: 'navigate', view: ViewState): void; // 导航请求
  (e: 'place-order'): void;               // 确认下单请求
  (e: 'update-quantity', cartId: string, delta: number): void; // 更新数量请求 (delta: +1/-1)
}>();

// --- 计算属性 (Computed Properties) ---

// 获取当前翻译
const t = computed(() => TRANSLATIONS[props.lang]);

/**
 * 计算订单小计 (Subtotal)
 * 以整数「分」累加，避免浮点元值累积出与后端相差一分钱的显示结果。
 */
const subtotalCents = computed(() => sumCents(props.cart));

/**
 * 计算应付总额 (Total)
 * 目前无税费或运费，等于小计。
 */
const totalCents = computed(() => subtotalCents.value);

// 按住顶部标题栏往下拖即可返回菜单 (和返回按钮一样)
const rootEl = ref<HTMLElement | null>(null);
const { handlers: dragHandlers } = useSheetDrag({
  sheet: rootEl,
  onDismiss: () => emit('navigate', 'order'),
});

</script>

<template>
  <div ref="rootEl" class="flex flex-col h-full bg-background-light relative z-40 shadow-sheet">
    <!-- Header (also the drag handle: swipe down to go back to the menu) -->
    <header class="relative flex items-center gap-3 px-4 md:px-8 py-3 md:py-4 bg-white border-b border-line shrink-0 sticky top-0 z-20 touch-none" v-on="dragHandlers">
      <div class="absolute top-1.5 left-1/2 -translate-x-1/2 h-1 w-10 bg-line rounded-full" aria-hidden="true"></div>
      <button
        type="button"
        @click="emit('navigate', 'order')"
        :aria-label="lang === 'cn' ? '返回' : 'Back'"
        class="size-11 rounded-full bg-cream/70 text-text-main flex items-center justify-center active:bg-cream"
      >
         <AppIcon name="arrow-left" class="text-xl" />
      </button>
      <h1 class="font-display text-xl md:text-2xl font-bold tracking-tight text-text-main">{{ t.reviewOrder }}</h1>
    </header>

    <!-- Cart list & summary -->
    <main class="flex-1 overflow-y-auto no-scrollbar p-4 md:p-8 pb-40 md:pb-10 flex flex-col md:flex-row gap-4 md:gap-6">

      <!-- Items -->
      <section class="flex-1 min-w-0">
         <div class="bg-white rounded-card shadow-card p-4 md:p-6">
            <h2 class="text-[13px] font-semibold text-text-sub mb-3">{{ t.items }} · {{ cart.length }}</h2>

            <!-- Empty State -->
            <div v-if="cart.length === 0" class="py-16 flex flex-col items-center text-text-sub">
               <AppIcon name="bag" class="text-4xl mb-3 opacity-60" />
               <p class="text-[15px] font-medium">{{ t.noOrders }}</p>
            </div>

            <!-- Cart Item Row -->
            <div
               v-else
               v-for="(item, idx) in cart"
               :key="item.cartId"
               class="flex gap-3.5 md:gap-4 py-4 border-b border-line last:border-0 animate-slide-up-content"
               :style="{ animationDelay: `${Math.min(idx, 6) * 40}ms` }"
            >
               <img :src="item.image" :alt="item.name" class="size-16 md:size-20 rounded-tile object-cover bg-cream shrink-0" decoding="async" />

               <div class="flex-1 min-w-0 flex flex-col">
                  <div class="flex items-start justify-between gap-3">
                     <h3 class="text-[15px] md:text-base font-semibold text-text-main line-clamp-1">
                        {{ lang === 'cn' ? item.nameCN : item.name }}
                     </h3>
                     <span class="text-[15px] md:text-base font-bold text-text-main tabular-nums shrink-0">¥{{ formatCents(toCents(item.price) * item.quantity) }}</span>
                  </div>
                  <!-- Options -->
                  <div class="flex flex-wrap gap-1.5 mt-1.5">
                     <span class="text-[12px] font-medium text-text-sub bg-cream px-2 py-0.5 rounded-full">
                        {{ lang === 'cn' ? (item.temperature === 'Hot' ? t.hot : t.iced) : item.temperature }}
                     </span>
                     <span v-if="item.sugar" class="text-[12px] font-medium text-text-sub bg-cream px-2 py-0.5 rounded-full">{{ item.sugar }}</span>
                  </div>

                  <!-- Quantity stepper -->
                  <div class="flex items-center justify-between mt-auto pt-2.5">
                     <span class="text-[12px] text-text-sub tabular-nums">¥{{ formatCents(toCents(item.price)) }} / {{ lang === 'cn' ? '杯' : 'ea' }}</span>
                     <div class="flex items-center bg-cream rounded-full p-1 gap-1.5">
                        <button
                           type="button"
                           @click="emit('update-quantity', item.cartId, -1)"
                           :aria-label="lang === 'cn' ? '减少' : 'Decrease'"
                           class="size-11 rounded-full bg-white text-text-main flex items-center justify-center shadow-sm outline-none"
                        >
                           <AppIcon name="minus" weight="bold" class="text-base" />
                        </button>
                        <span class="w-6 text-center text-base font-bold text-text-main tabular-nums">{{ item.quantity }}</span>
                        <button
                           type="button"
                           @click="emit('update-quantity', item.cartId, 1)"
                           :aria-label="lang === 'cn' ? '增加' : 'Increase'"
                           class="size-11 rounded-full bg-primary text-white flex items-center justify-center outline-none active:bg-primary-dark"
                        >
                           <AppIcon name="plus" weight="bold" class="text-base" />
                        </button>
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </section>

      <!-- Summary -->
      <aside class="md:w-80 lg:w-96 shrink-0">
         <div class="bg-white rounded-card shadow-card p-5 md:p-6 flex flex-col gap-4 md:sticky md:top-0">
            <h3 class="text-[13px] font-semibold text-text-sub">{{ t.pay }}</h3>
            <div class="flex justify-between text-[15px] text-text-sub">
               <span>{{ t.subtotal }}</span>
               <span class="tabular-nums">¥{{ formatCents(subtotalCents) }}</span>
            </div>
            <div class="h-px bg-line"></div>
            <div class="flex items-baseline justify-between text-text-main">
               <span class="text-[15px] font-semibold">{{ t.total }}</span>
               <span class="text-3xl font-bold tabular-nums"><span class="text-lg font-semibold mr-0.5">¥</span>{{ formatCents(totalCents) }}</span>
            </div>

            <!-- Pay Button (iPad) -->
            <button
               type="button"
               @click="emit('place-order')"
               :disabled="cart.length === 0 || placing"
               class="hidden md:flex items-center justify-center gap-2 w-full h-14 rounded-full bg-primary text-white font-semibold text-[17px] disabled:opacity-60 active:bg-primary-dark outline-none"
            >
               <template v-if="placing">
                  <span class="size-5 border-2 border-white/30 border-t-white rounded-full animate-spin" aria-hidden="true"></span>
                  {{ t.placing }}
               </template>
               <template v-else>
                  {{ lang === 'cn' ? '支付' : 'Pay' }} ¥{{ formatCents(totalCents) }}
               </template>
            </button>

            <p class="flex items-center justify-center gap-1.5 text-[12px] text-text-sub">
               <AppIcon name="lock" class="text-sm" />
               {{ t.securePayment }}
            </p>
         </div>
      </aside>
    </main>

    <!-- Pay Button (phone): pinned to the bottom -->
    <div class="md:hidden absolute bottom-0 inset-x-0 bg-white border-t border-line px-4 pt-3 pb-[max(env(safe-area-inset-bottom),16px)] z-30">
       <button
           type="button"
           @click="emit('place-order')"
           :disabled="cart.length === 0 || placing"
           class="w-full h-14 rounded-full bg-primary text-white font-semibold text-[17px] flex items-center justify-center gap-2 disabled:opacity-60 active:bg-primary-dark outline-none"
        >
           <template v-if="placing">
              <span class="size-5 border-2 border-white/30 border-t-white rounded-full animate-spin" aria-hidden="true"></span>
              {{ t.placing }}
           </template>
           <template v-else>
              {{ lang === 'cn' ? '支付' : 'Pay' }} ¥{{ formatCents(totalCents) }}
           </template>
        </button>
    </div>
  </div>
</template>
