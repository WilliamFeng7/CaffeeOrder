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
    <header class="relative flex items-center gap-3 px-4 md:px-8 py-3 md:py-4 bg-surface-light border-b border-line shrink-0 sticky top-0 z-20 touch-none" v-on="dragHandlers">
      <div class="absolute top-1.5 left-1/2 -translate-x-1/2 h-1 w-9 bg-line rounded-full" aria-hidden="true"></div>
      <button
        type="button"
        @click="emit('navigate', 'order')"
        :aria-label="lang === 'cn' ? '返回' : 'Back'"
        class="size-11 rounded-full text-text-main flex items-center justify-center active:bg-cream"
      >
         <AppIcon name="arrow-left" class="text-xl" />
      </button>
      <h1 class="font-serif text-[22px] md:text-[26px] font-medium text-text-main">{{ t.reviewOrder }}</h1>
    </header>

    <main class="flex-1 overflow-y-auto no-scrollbar px-5 md:px-10 pt-6 pb-40 md:pb-10 flex flex-col md:flex-row gap-8 md:gap-10">

      <!-- Items -->
      <section class="flex-1 min-w-0">
         <p class="text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub pb-3 border-b border-line">{{ t.items }} · {{ cart.length }}</p>

         <div v-if="cart.length === 0" class="py-16 flex flex-col items-center text-text-sub">
            <AppIcon name="bag" class="text-3xl mb-3" />
            <p class="text-[15px]">{{ t.noOrders }}</p>
         </div>

         <div
            v-else
            v-for="(item, idx) in cart"
            :key="item.cartId"
            class="flex gap-4 py-5 border-b border-line animate-slide-up-content"
            :style="{ animationDelay: `${Math.min(idx, 6) * 45}ms` }"
         >
            <img :src="item.image" :alt="item.name" class="size-[72px] md:size-20 rounded-tile object-cover bg-cream shrink-0" decoding="async" />

            <div class="flex-1 min-w-0 flex flex-col">
               <div class="flex items-start justify-between gap-3">
                  <h3 class="text-[16px] font-medium text-text-main line-clamp-1">{{ lang === 'cn' ? item.nameCN : item.name }}</h3>
                  <span class="text-[16px] font-medium text-text-main tabular-nums shrink-0">¥{{ formatCents(toCents(item.price) * item.quantity) }}</span>
               </div>
               <p class="mt-1 text-[13px] text-text-sub">
                  {{ lang === 'cn' ? (item.temperature === 'Hot' ? t.hot : t.iced) : item.temperature }}<template v-if="item.sugar"> · {{ item.sugar }}</template>
               </p>

               <div class="flex items-center justify-between mt-auto pt-3">
                  <span class="text-[13px] text-text-sub tabular-nums">¥{{ formatCents(toCents(item.price)) }} / {{ lang === 'cn' ? '杯' : 'ea' }}</span>
                  <div class="flex items-center gap-1">
                     <button
                        type="button"
                        @click="emit('update-quantity', item.cartId, -1)"
                        :aria-label="lang === 'cn' ? '减少' : 'Decrease'"
                        class="size-11 rounded-full border border-line text-text-main flex items-center justify-center outline-none"
                     >
                        <AppIcon name="minus" class="text-base" />
                     </button>
                     <span class="w-8 text-center text-[16px] font-medium text-text-main tabular-nums">{{ item.quantity }}</span>
                     <button
                        type="button"
                        @click="emit('update-quantity', item.cartId, 1)"
                        :aria-label="lang === 'cn' ? '增加' : 'Increase'"
                        class="size-11 rounded-full border border-line text-text-main flex items-center justify-center outline-none active:bg-primary active:border-primary active:text-white"
                     >
                        <AppIcon name="plus" class="text-base" />
                     </button>
                  </div>
               </div>
            </div>
         </div>
      </section>

      <!-- Summary -->
      <aside class="md:w-80 lg:w-[360px] shrink-0">
         <div class="md:sticky md:top-0 bg-surface-light rounded-card border border-line p-6 flex flex-col gap-4">
            <p class="text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub">{{ t.pay }}</p>
            <div class="flex justify-between text-[15px] text-text-sub">
               <span>{{ t.subtotal }}</span>
               <span class="tabular-nums">¥{{ formatCents(subtotalCents) }}</span>
            </div>
            <div class="h-px bg-line"></div>
            <div class="flex items-baseline justify-between text-text-main">
               <span class="text-[15px]">{{ t.total }}</span>
               <span class="font-serif text-[32px] font-medium tabular-nums">¥{{ formatCents(totalCents) }}</span>
            </div>

            <!-- Pay (iPad) -->
            <button
               type="button"
               @click="emit('place-order')"
               :disabled="cart.length === 0 || placing"
               class="hidden md:flex items-center justify-center gap-2 w-full h-14 rounded-full bg-primary text-white text-[16px] font-medium disabled:opacity-60 active:bg-primary-dark outline-none"
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

    <!-- Pay (phone): pinned to the bottom -->
    <div class="md:hidden absolute bottom-0 inset-x-0 bg-surface-light border-t border-line px-5 pt-3 pb-[max(env(safe-area-inset-bottom),16px)] z-30">
       <button
           type="button"
           @click="emit('place-order')"
           :disabled="cart.length === 0 || placing"
           class="w-full h-14 rounded-full bg-primary text-white text-[16px] font-medium flex items-center justify-center gap-2 disabled:opacity-60 active:bg-primary-dark outline-none"
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
