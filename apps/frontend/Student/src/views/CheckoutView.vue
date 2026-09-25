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

import { computed } from 'vue';
import { TRANSLATIONS } from '../data';
import { formatCents, toCents, sumCents } from '../utils/money';
import type { CartItem, ViewState, Language } from '../types';

// --- Props & Events ---
const props = defineProps<{
  cart: CartItem[]; // 购物车数据源
  lang: Language;   // 当前语言
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

</script>

<template>
  <div class="flex flex-col h-full bg-background-light relative z-40">
    <!-- Header Navigation -->
    <!-- 顶部导航: 返回按钮和标题 -->
    <header class="flex items-center px-6 py-6 md:px-10 md:py-8 bg-white/80 backdrop-blur-md shadow-sm shrink-0 sticky top-0 z-20 transition-all duration-300">
      <button 
        @click="emit('navigate', 'order')" 
        class="flex items-center justify-center size-12 md:size-14 rounded-full bg-gray-50 active:bg-gray-100 transition-all duration-500 ease-luxury active:scale-75 outline-none"
      >
         <span class="material-symbols-rounded text-text-main text-xl md:text-2xl">arrow_back</span>
      </button>
      <h1 class="text-2xl md:text-3xl font-[900] ml-4 text-text-main tracking-tight">{{ t.reviewOrder }}</h1>
    </header>

    <!-- Main Content: Cart List & Payment Summary -->
    <main class="flex-1 overflow-y-auto no-scrollbar p-6 md:p-10 pb-40 flex flex-col md:flex-row gap-8">
      
      <!-- Left Column: Cart Items List -->
      <!-- 左侧: 商品清单 -->
      <div class="flex-1 space-y-6">
         <div class="bg-white rounded-[32px] p-6 md:p-8 shadow-[0_8px_30px_-8px_rgba(0,0,0,0.05)] min-h-[300px]">
            <div class="flex items-center justify-between mb-6">
               <h2 class="text-lg font-black text-text-main uppercase tracking-widest opacity-80">{{ t.items }} ({{ cart.length }})</h2>
            </div>
            
            <div class="space-y-8">
               <!-- Empty State -->
               <div v-if="cart.length === 0" class="flex flex-col items-center justify-center py-20 text-gray-300">
                  <span class="material-symbols-rounded text-6xl mb-4 opacity-30">remove_shopping_cart</span>
                  <p class="font-bold text-sm uppercase tracking-widest">{{ t.noOrders }}</p>
               </div>

               <!-- Cart Item Row -->
               <div 
                  v-else 
                  v-for="(item, idx) in cart" 
                  :key="item.cartId" 
                  class="flex gap-4 md:gap-6 border-b border-gray-50 pb-6 last:border-0 last:pb-0 animate-slide-up-content" 
                  :style="{ animationDelay: `${idx * 50}ms` }"
               >
                  <!-- Item Image -->
                  <div class="size-20 md:size-24 rounded-2xl bg-gray-100 bg-cover bg-center shrink-0 shadow-inner" :style="{ backgroundImage: `url(${item.image})` }"></div>
                  
                  <!-- Item Details -->
                  <div class="flex-1 flex flex-col justify-between py-1">
                     <div>
                       <!-- Name & Subtotal -->
                       <div class="flex justify-between items-start mb-1">
                          <h3 class="text-base md:text-lg font-[800] text-text-main line-clamp-1">
                             {{ lang === 'cn' ? item.nameCN : item.name }}
                          </h3>
                          <span class="font-[900] text-base text-primary">¥{{ formatCents(toCents(item.price) * item.quantity) }}</span>
                       </div>
                       <!-- Spec Tags -->
                       <div class="flex flex-wrap gap-1.5 opacity-60 mb-2">
                           <!-- Size Removed -->

                          <!-- Temp -->
                          <span class="text-[10px] font-bold text-text-sub bg-gray-100 px-2 py-0.5 rounded">
                             {{ lang === 'cn' ? (item.temperature === 'Hot' ? t.hot : t.iced) : item.temperature }}
                          </span>
                          <!-- Sugar -->
                          <span v-if="item.sugar" class="text-[10px] font-bold text-text-sub bg-gray-100 px-2 py-0.5 rounded">{{ item.sugar }}</span>

                       </div>
                     </div>

                     <!-- Quantity Controller -->
                     <div class="flex items-center justify-between mt-1">
                        <div class="flex items-center bg-gray-50 rounded-full p-1 gap-3 shadow-inner">
                           <!-- Decrease -->
                           <button 
                              @click="emit('update-quantity', item.cartId, -1)" 
                              class="size-9 rounded-full bg-white text-text-main flex items-center justify-center shadow-sm transition-all duration-300 ease-luxury active:scale-75 outline-none"
                           >
                              <span class="material-symbols-rounded text-sm font-bold">remove</span>
                           </button>
                           <!-- Count -->
                           <span class="font-black text-text-main text-sm w-4 text-center tabular-nums">{{ item.quantity }}</span>
                           <!-- Increase -->
                           <button 
                              @click="emit('update-quantity', item.cartId, 1)" 
                              class="size-9 rounded-full bg-primary text-white flex items-center justify-center shadow-md transition-all duration-300 ease-luxury active:scale-75 outline-none"
                           >
                              <span class="material-symbols-rounded text-sm font-bold">add</span>
                           </button>
                        </div>
                        <!-- Unit Price -->
                        <span class="text-[10px] font-bold text-gray-400">¥{{ formatCents(toCents(item.price)) }} / ea</span>
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </div>

      <!-- Right Column: Summary & Pay -->
      <!-- 右侧: 结算概览 -->
      <div class="md:w-96 flex flex-col gap-6">
         <div class="bg-white rounded-[32px] p-6 md:p-8 shadow-[0_8px_30px_-8px_rgba(0,0,0,0.05)] flex flex-col gap-6 md:sticky md:top-28">
            <h3 class="font-black text-xl tracking-tight">{{ t!.pay }}</h3>
            
            <!-- Price Breakdown -->
            <div class="space-y-3">
               <div class="flex justify-between text-text-sub text-sm font-bold">
                  <span>{{ t.subtotal }}</span>
                  <span>¥{{ formatCents(subtotalCents) }}</span>
               </div>
               <div class="h-px bg-gray-100 my-2"></div>
                <div class="flex justify-between text-3xl font-sans font-black text-[#103E32] tracking-tighter">
                   <span>{{ t.total }}</span>
                   <span class="font-sans">¥{{ formatCents(totalCents) }}</span>
                </div>
            </div>

            <!-- Pay Button (Desktop) -->
            <button 
               @click="emit('place-order')"
               :disabled="cart.length === 0"
               class="hidden md:block w-full h-[72px] rounded-[32px] font-sans font-black text-2xl shadow-xl mt-4 transition-all duration-500 ease-luxury active:scale-[0.96] disabled:opacity-50 disabled:grayscale outline-none text-white bg-[#103E32] shadow-[#103E32]/30"
            >
               {{ lang === 'cn' ? '支付' : 'Pay' }} <span class="bg-white/10 px-2 py-0.5 rounded-lg ml-1 font-sans">¥{{ formatCents(totalCents) }}</span>
            </button>
            
            <p class="text-center text-[9px] font-bold text-gray-300 uppercase tracking-widest">{{ t.securePayment }}</p>
         </div>
      </div>
    </main>

    <!-- Mobile Sticky Pay Button -->
    <!-- 移动端底部悬浮支付按钮 -->
    <div class="md:hidden absolute bottom-0 left-0 w-full bg-white p-4 pb-[env(safe-area-inset-bottom,20px)] border-t border-gray-100 z-30 shadow-[0_-10px_30px_rgba(0,0,0,0.05)]">
       <button 
           @click="emit('place-order')"
           :disabled="cart.length === 0"
           class="w-full h-16 rounded-[32px] font-sans font-black text-xl shadow-lg active:scale-[0.96] transition-all duration-500 ease-luxury disabled:opacity-50 outline-none flex items-center justify-center gap-2 text-white bg-[#103E32] shadow-[#103E32]/20"
        >
           {{ lang === 'cn' ? '支付' : 'Pay' }} <span class="bg-white/20 px-3 py-1 rounded-xl text-white text-lg font-sans font-bold">¥{{ formatCents(totalCents) }}</span>
        </button>
    </div>
  </div>
</template>
