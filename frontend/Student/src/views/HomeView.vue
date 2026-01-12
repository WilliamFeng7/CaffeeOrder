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

import { computed, onMounted } from 'vue';
import { TRANSLATIONS, PRODUCTS } from '../data';
import { api } from '../api';
import type { Product, Language, TabState } from '../types';

// ...

// Fetch initial data



// 定义组件 Props (Props Definition)
const props = defineProps<{
  lang: Language; // 当前语言环境
  userName?: string; // 当前登录用户名 (用于个性化问候)
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

</script>

<template>
  <div class="flex-1 h-full bg-background-light overflow-y-auto scroll-smooth-touch no-scrollbar pb-40">
    <div class="p-6 md:p-12 space-y-6 pt-12 md:pt-20 max-w-5xl mx-auto">
      
      <!-- Logo & Header Section -->
      <div class="flex flex-col gap-1">
         <!-- Brand Status -->
         <div class="flex items-center gap-3 mb-2 opacity-0 animate-slide-down-content transform-gpu" style="animation-delay: 0ms">
            <span class="material-symbols-rounded text-primary text-3xl">storefront</span>
            <span class="text-[12px] font-black text-text-sub uppercase tracking-[0.3em]">{{ t.downtownCafe }}</span>
            <span class="ml-auto bg-primary text-white text-[10px] font-black px-4 py-2 rounded-full flex items-center gap-2 shadow-lg shadow-primary/20 animate-scale-in select-none" style="animation-delay: 800ms">
               <span class="size-1.5 rounded-full bg-white animate-pulse"></span>
               OPEN
            </span>
         </div>
         
         <!-- Welcome Title -->
         <div class="relative overflow-hidden pb-4">
           <h1 class="text-6xl md:text-8xl font-sans font-black text-[#103E32] leading-[0.95] tracking-tighter animate-text-reveal transform-gpu mb-2" style="animation-delay: 300ms">
              {{ t.goodMorning }}
           </h1>
         </div>
         
         <!-- Username Display -->
         <div class="relative overflow-hidden pb-2">
           <h1 class="text-4xl md:text-5xl font-bold text-[#103E32] italic font-serif leading-[1.05] tracking-wide animate-text-reveal transform-gpu" style="animation-delay: 450ms">
              {{ displayName }}
           </h1>
         </div>
      </div>

      <!-- Featured Product Card -->
      <div 
         class="relative h-[280px] md:h-[380px] lg:h-[440px] rounded-[36px] md:rounded-[48px] overflow-hidden shadow-[0_30px_80px_-20px_rgba(0,0,0,0.2)] animate-slide-up-content active:scale-[0.98] transition-all duration-700 ease-luxury transform-gpu group cursor-pointer"
         style="animation-delay: 600ms"
         @click="featuredProduct.inventoryCount !== 0 && emit('quick-add', featuredProduct)"
      >
         <!-- Sold Out Overlay -->
         <div v-if="featuredProduct.inventoryCount === 0" class="absolute inset-0 z-50 bg-black/40 backdrop-blur-[2px] flex items-center justify-center pointer-events-none">
            <div class="bg-red-500 text-white px-6 py-2 rounded-full font-black uppercase tracking-widest shadow-xl rotate-[-10deg] border-4 border-white">Sold Out</div>
         </div>

         <!-- Image Container ... -->
         <div class="absolute inset-0 w-full h-full overflow-hidden rounded-[48px] bg-gray-900">
            <img 
               :src="featuredProduct.image" 
               class="w-full h-full object-cover opacity-90 transition-transform duration-[1.5s] ease-luxury" 
               :class="{'grayscale': featuredProduct.inventoryCount === 0}"
               :alt="featuredProduct.name"
            />
         </div>
         
         <!-- Gradient Overlays ... -->
         <div class="absolute inset-0 bg-gradient-to-t from-[#0A2921] via-transparent to-transparent opacity-90"></div>
         <div class="absolute inset-0 bg-gradient-to-b from-[#0A2921]/10 to-transparent"></div>
         
         <!-- Content Info -->
         <div class="absolute bottom-6 left-6 right-6 md:bottom-10 md:left-10 md:right-10 flex justify-between items-end z-10">
            <div class="max-w-xl">
               <span class="bg-[#DCCA98] text-[#0C1F1A] text-[10px] font-black uppercase tracking-[0.2em] px-4 py-2 rounded-full mb-4 inline-block shadow-lg shadow-black/20 animate-fade-in backdrop-blur-sm" style="animation-delay: 1000ms">{{ t.bestSeller }}</span>
               <h2 class="text-3xl md:text-5xl font-sans font-black text-white leading-[1.1] mb-2 md:mb-3 tracking-tighter drop-shadow-lg">{{ lang === 'cn' ? featuredProduct.nameCN : featuredProduct.name }}</h2>
               <p class="text-white/80 text-base font-medium line-clamp-2 leading-relaxed opacity-0 animate-slide-up-content max-w-sm" style="animation-delay: 1100ms">{{ lang === 'cn' ? featuredProduct.descriptionCN : featuredProduct.description }}</p>
            </div>
            
            <!-- Quick Add Button -->
            <button class="size-14 md:size-20 rounded-[24px] md:rounded-[32px] bg-white text-[#103E32] flex items-center justify-center shadow-2xl transition-all duration-500 ease-luxury active:scale-90 active:rotate-90 group-hover:scale-110 shrink-0">
               <span class="material-symbols-rounded text-4xl font-light">add</span>
            </button>
         </div>
      </div>

      <!-- Trending Section -->
      <div class="animate-fade-in" style="animation-delay: 800ms">
         <!-- Section Header -->
         <div class="flex items-center justify-between mb-6">
            <h2 class="text-3xl font-black text-text-main tracking-tight animate-slide-up-content" style="animation-delay: 900ms">{{ t.trendingNow }}</h2>
            <button @click="emit('navigate', 'order')" class="text-primary font-bold text-sm flex items-center gap-1 py-3 px-4 -mr-4 active:bg-gray-100 rounded-full transition-all duration-500 ease-luxury animate-slide-up-content active:scale-90" style="animation-delay: 1000ms">
               {{ t.seeAll }}
               <span class="material-symbols-rounded text-xl">arrow_forward</span>
            </button>
         </div>
         
         <!-- Trending Grid -->
         <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div 
               v-for="(p, i) in trending"
               :key="p.id" 
               @click="p.inventoryCount !== 0 && emit('quick-add', p)"
               data-testid="product-card"
               class="bg-white p-4 pb-5 rounded-[40px] shadow-sm active:scale-[0.96] transition-all duration-500 ease-luxury animate-slide-up-content transform-gpu border border-white cursor-pointer relative overflow-hidden"
               :class="{'opacity-70 pointer-events-none': p.inventoryCount === 0}"
               :style="{ animationDelay: `${1000 + i * 120}ms` }"
            >
               <!-- Sold Out Badge -->
               <div v-if="p.inventoryCount === 0" class="absolute top-4 left-4 z-20 bg-red-500 text-white text-[10px] font-black px-3 py-1 rounded-full shadow-lg">SOLD OUT</div>

               <!-- Card Image -->
               <div class="aspect-square rounded-[32px] overflow-hidden mb-4 bg-background-light relative shadow-inner group">
                  <img :src="p.image" class="w-full h-full object-cover transition-transform duration-700 ease-luxury group-hover:scale-110" :class="{'grayscale': p.inventoryCount === 0}" :alt="p.name" />
                  
                  <!-- Floating Add Icon -->
                  <div v-if="p.inventoryCount !== 0" class="absolute top-3 right-3 size-10 rounded-full bg-white/90 backdrop-blur-md flex items-center justify-center shadow-sm transition-transform duration-500 ease-luxury active:scale-75 active:rotate-90 group-active:scale-90">
                     <span class="material-symbols-rounded text-primary font-bold">add</span>
                  </div>
               </div>
               
               <!-- Card Info -->
               <h3 class="text-lg font-black text-text-main leading-tight mb-1 line-clamp-1 px-1">{{ lang === 'cn' ? p.nameCN : p.name }}</h3>
               <div class="flex items-center justify-between px-1">
                  <!-- Price formatted to 2 decimals -->
                  <span class="text-xl font-black text-primary">¥{{ Number(p.price).toFixed(2) }}</span>
               </div>
            </div>
         </div>
      </div>
    </div>
  </div>
</template>
