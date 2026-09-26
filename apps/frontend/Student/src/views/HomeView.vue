<script setup lang="ts">
/**
 * HomeView.vue
 * 
 * 首页视图组件 (Home View Component).
 * 
 * 主要功能 (Core Features):
 * 1. 欢迎标语 (Welcome Banner): 根据时间或写死的欢迎语展示。
 * 2. 推荐位 (Featured Item): 展示主推商品 (通常是列表中的第2个商品)。
 * 3. 热门推荐 (Trending List): 展示列表中的第3-5个商品。
 * 4. 快速导航 (Quick Nav): 跳转到完整菜单。
 */

import { computed } from 'vue';
import { TRANSLATIONS, PRODUCTS } from '../data';
import type { Product, Language, TabState } from '../types';

// ...

// Fetch initial data



// 定义组件 Props (Props Definition)
const props = defineProps<{
  lang: Language; // 当前语言环境
  userName?: string; // 当前登录用户名 (用于个性化问候)
  shopOpen?: boolean; // 店铺是否营业 (来自 /shop/status)
}>();

// 定义组件 Events (Events Definition)
const emit = defineEmits<{
  (e: 'navigate', tab: TabState): void; // 导航跳转请求
  (e: 'quick-add', product: Product): void; // 快速点击商品 (通常打开详情弹窗)
}>();

// 计算属性：获取当前语言的翻译包
const t = computed(() => TRANSLATIONS[props.lang]);

/**
 * 获取主推商品 (Featured Product)
 * 逻辑:
 * 1. 优先尝试获取商品列表的第 2 个 (Index 1) 作为主推。
 * 2. 如果不存在，降级使用第 1 个 (Index 0)。
 * 3. 如果列表为空 (极端情况/加载中)，使用占位数据兜底，防止页面崩坏。
 */
const featuredProduct = computed(() => PRODUCTS[1] || PRODUCTS[0] || {
  id: 'placeholder',
  name: 'Welcome',
  nameCN: '欢迎',
  description: 'Start your order now.',
  descriptionCN: '现在开始点餐。',
  price: 0,
  category: 'coffee',
  image: 'https://placehold.co/600x400',
});

/**
 * 获取热门趋势商品 (Trending Products)
 * 逻辑:
 * 取商品列表的下标 2, 3, 4 (即第 3 到第 5 个商品) 作为热门推荐展示。
 * 如果商品不足，则回退取前 3 个。
 */
const trending = computed(() => PRODUCTS.length > 2 ? PRODUCTS.slice(2, 5) : PRODUCTS.slice(0, 3));

// 计算显示的用户名，如果未登录或未传值，默认显示 'Otiaer'
const displayName = computed(() => props.userName ? props.userName : 'Otiaer');

// 问候语跟随时间 (下午不再显示「早上好」)
const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 11) return t.value.goodMorning;
  if (hour < 18) return t.value.goodAfternoon;
  return t.value.goodEvening;
});

const isOpen = computed(() => props.shopOpen !== false);

</script>

<template>
  <div class="flex-1 h-full bg-background-light overflow-y-auto scroll-smooth-touch no-scrollbar pb-32">
    <div class="px-5 md:px-10 pt-8 md:pt-12 space-y-6 max-w-5xl mx-auto">

      <!-- Logo & Header Section -->
      <header class="flex flex-col gap-1">
         <!-- Brand Status -->
         <div class="flex items-center gap-3 mb-3 animate-slide-down-content">
            <span class="material-symbols-rounded text-primary text-[28px]" aria-hidden="true">storefront</span>
            <span class="text-[12px] font-black text-text-sub uppercase tracking-[0.3em]">{{ t.downtownCafe }}</span>
            <span
               class="ml-auto text-[10px] font-black uppercase tracking-wider px-3.5 py-1.5 rounded-full flex items-center gap-2 select-none animate-scale-in"
               :class="isOpen ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'bg-gray-200 text-gray-600'"
               style="animation-delay: 120ms"
            >
               <span class="size-1.5 rounded-full" :class="isOpen ? 'bg-emerald-300' : 'bg-gray-400'" aria-hidden="true"></span>
               {{ isOpen ? t.open : t.closed }}
            </span>
         </div>

         <!-- Welcome Title -->
         <h1 class="text-[44px] md:text-7xl font-sans font-black text-[#103E32] leading-[0.95] tracking-tighter animate-text-reveal" style="animation-delay: 60ms">
            {{ greeting }}
         </h1>

         <!-- Username Display -->
         <p class="text-3xl md:text-4xl font-bold text-[#103E32] italic font-serif leading-tight tracking-wide pb-1 animate-text-reveal" style="animation-delay: 120ms">
            {{ displayName }}
         </p>
      </header>

      <!-- Featured + Trending: stacked on phones, side by side on iPad landscape -->
      <div class="grid gap-6 lg:grid-cols-5 lg:items-start">

         <!-- Featured Product Card -->
         <div
            class="lg:col-span-3 relative h-[220px] md:h-[300px] lg:h-[400px] rounded-[32px] md:rounded-[40px] overflow-hidden bg-gray-900 shadow-[0_24px_60px_-20px_rgba(0,0,0,0.3)] cursor-pointer transition-transform duration-200 ease-out active:scale-[0.98] animate-slide-up-content"
            style="animation-delay: 160ms"
            @click="featuredProduct.inventoryCount !== 0 && emit('quick-add', featuredProduct)"
         >
            <!-- Sold Out Overlay -->
            <div v-if="featuredProduct.inventoryCount === 0" class="absolute inset-0 z-50 bg-black/40 flex items-center justify-center pointer-events-none">
               <div class="bg-red-500 text-white px-6 py-2 rounded-full font-black uppercase tracking-widest shadow-xl rotate-[-10deg] border-4 border-white">Sold Out</div>
            </div>

            <img
               :src="featuredProduct.image"
               class="absolute inset-0 w-full h-full object-cover opacity-90"
               :class="{'grayscale': featuredProduct.inventoryCount === 0}"
               :alt="featuredProduct.name"
            />

            <!-- Gradient Overlay -->
            <div class="absolute inset-0 bg-gradient-to-t from-[#0A2921] via-[#0A2921]/20 to-transparent"></div>

            <!-- Content Info -->
            <div class="absolute bottom-5 left-5 right-5 md:bottom-8 md:left-8 md:right-8 flex justify-between items-end gap-4 z-10">
               <div class="min-w-0">
                  <span class="bg-[#DCCA98] text-[#0C1F1A] text-[10px] font-black uppercase tracking-[0.2em] px-3 py-1.5 rounded-full mb-3 inline-block shadow-lg shadow-black/20 animate-fade-in" style="animation-delay: 240ms">{{ t.bestSeller }}</span>
                  <h2 class="text-3xl md:text-5xl font-sans font-black text-white leading-[1.05] tracking-tighter drop-shadow-lg line-clamp-2">{{ lang === 'cn' ? featuredProduct.nameCN : featuredProduct.name }}</h2>
                  <p class="text-white/80 text-sm md:text-base font-medium line-clamp-1 md:line-clamp-2 leading-relaxed mt-1.5 max-w-sm animate-slide-up-content" style="animation-delay: 240ms">{{ lang === 'cn' ? featuredProduct.descriptionCN : featuredProduct.description }}</p>
               </div>

               <!-- Quick Add Button -->
               <button
                  v-if="featuredProduct.inventoryCount !== 0"
                  type="button"
                  :aria-label="t.addToCart"
                  class="size-14 md:size-16 rounded-[22px] md:rounded-[26px] bg-white text-[#103E32] flex items-center justify-center shadow-2xl shrink-0"
               >
                  <span class="material-symbols-rounded text-3xl md:text-4xl font-light" aria-hidden="true">add</span>
               </button>
            </div>
         </div>

         <!-- Trending Section -->
         <section class="lg:col-span-2 animate-fade-in" style="animation-delay: 200ms">
            <!-- Section Header -->
            <div class="flex items-center justify-between mb-3 md:mb-4">
               <h2 class="text-2xl md:text-3xl font-black text-text-main tracking-tight">{{ t.trendingNow }}</h2>
               <button type="button" @click="emit('navigate', 'order')" class="text-primary font-bold text-sm flex items-center gap-1 py-2.5 px-3 -mr-3 rounded-full active:bg-gray-100">
                  {{ t.seeAll }}
                  <span class="material-symbols-rounded text-xl" aria-hidden="true">arrow_forward</span>
               </button>
            </div>

            <!-- Trending List: compact rows on phones and beside the featured card, tiles on iPad portrait -->
            <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-1 gap-3">
               <div
                  v-for="(p, i) in trending"
                  :key="p.id"
                  @click="p.inventoryCount !== 0 && emit('quick-add', p)"
                  data-testid="product-card"
                  class="bg-white p-3 rounded-[24px] shadow-sm flex items-center gap-4 md:flex-col md:items-stretch md:gap-3 lg:flex-row lg:items-center lg:gap-4 cursor-pointer relative transition-transform duration-200 ease-out active:scale-[0.98] animate-slide-up-content"
                  :class="{'opacity-60 pointer-events-none': p.inventoryCount === 0}"
                  :style="{ animationDelay: `${240 + i * 40}ms` }"
               >
                  <!-- Card Image -->
                  <div class="w-16 h-16 md:w-full md:h-auto md:aspect-[4/3] lg:w-20 lg:h-20 lg:aspect-auto rounded-[18px] overflow-hidden bg-background-light shrink-0">
                     <img :src="p.image" class="w-full h-full object-cover" :class="{'grayscale': p.inventoryCount === 0}" :alt="p.name" loading="lazy" />
                  </div>

                  <!-- Card Info -->
                  <div class="min-w-0 flex-1 md:px-1 lg:px-0">
                     <h3 class="text-base md:text-lg font-black text-text-main leading-tight line-clamp-1">{{ lang === 'cn' ? p.nameCN : p.name }}</h3>
                     <p v-if="p.inventoryCount === 0" class="text-[11px] font-black text-red-500 uppercase tracking-wider mt-1">Sold Out</p>
                     <p v-else class="text-lg font-black text-primary mt-0.5">¥{{ Number(p.price).toFixed(2) }}</p>
                  </div>

                  <span v-if="p.inventoryCount !== 0" class="size-10 rounded-full bg-primary/10 text-primary flex md:hidden lg:flex items-center justify-center shrink-0" aria-hidden="true">
                     <span class="material-symbols-rounded font-bold">add</span>
                  </span>
               </div>
            </div>
         </section>
      </div>
    </div>
  </div>
</template>
