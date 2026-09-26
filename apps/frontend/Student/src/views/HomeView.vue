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

import AppIcon from '@shared/components/AppIcon.vue';
import { computed, ref, onActivated } from 'vue';
import { TRANSLATIONS, PRODUCTS } from '../data';
import type { Product, Language, TabState } from '../types';
import { useKeepScroll } from '../composables/useKeepScroll';

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
  image: '',
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

// 问候语跟随时间 (下午不再显示「早上好」)；标签页被缓存，所以每次回到首页时刷新一下
const hour = ref(new Date().getHours());
onActivated(() => { hour.value = new Date().getHours(); });
const greeting = computed(() => {
  if (hour.value < 5) return t.value.goodEvening;
  if (hour.value < 11) return t.value.goodMorning;
  if (hour.value < 18) return t.value.goodAfternoon;
  return t.value.goodEvening;
});

const isOpen = computed(() => props.shopOpen !== false);

const { scroller, onScroll } = useKeepScroll();

</script>

<template>
  <div ref="scroller" @scroll.passive="onScroll" class="flex-1 h-full bg-background-light overflow-y-auto scroll-smooth-touch no-scrollbar pb-32">
    <div class="px-5 md:px-10 pt-6 md:pt-10 space-y-6 md:space-y-8 max-w-5xl mx-auto">

      <!-- Brand & Greeting -->
      <header class="space-y-4 md:space-y-5">
         <div class="flex items-center gap-2.5 animate-fade-in">
            <span class="size-9 rounded-full bg-primary text-white flex items-center justify-center shrink-0">
               <AppIcon name="coffee" weight="fill" class="text-lg" />
            </span>
            <span class="font-serif text-lg font-semibold text-text-main">{{ t.downtownCafe }}</span>
            <span
               class="ml-auto h-8 px-3 rounded-full text-[12px] font-semibold flex items-center gap-1.5"
               :class="isOpen ? 'bg-primary-soft text-primary' : 'bg-cream text-text-sub'"
            >
               <span class="size-1.5 rounded-full" :class="isOpen ? 'bg-primary' : 'bg-text-sub'" aria-hidden="true"></span>
               {{ isOpen ? t.open : t.closed }}
            </span>
         </div>

         <div class="animate-slide-up-content" style="animation-delay: 40ms">
            <h1 class="font-display text-[30px] md:text-5xl font-bold tracking-tight leading-tight text-text-main">
               {{ greeting }} <span class="font-serif italic font-semibold text-primary">{{ displayName }}</span>
            </h1>
            <p class="mt-1.5 text-[15px] md:text-lg text-text-sub">{{ t.homeSubtitle }}</p>
         </div>
      </header>

      <!-- Featured + Trending: stacked on phones, side by side on iPad landscape -->
      <div class="grid gap-6 lg:grid-cols-5 lg:items-start">

         <!-- Featured Product Card -->
         <div
            class="lg:col-span-3 relative h-[220px] md:h-[300px] lg:h-[380px] rounded-card overflow-hidden bg-text-main shadow-card cursor-pointer transition-transform duration-200 ease-out active:scale-[0.99] animate-slide-up-content"
            style="animation-delay: 80ms"
            @click="featuredProduct.inventoryCount !== 0 && emit('quick-add', featuredProduct)"
         >
            <img
               v-if="featuredProduct.image"
               :src="featuredProduct.image"
               class="absolute inset-0 w-full h-full object-cover"
               :class="{'grayscale': featuredProduct.inventoryCount === 0}"
               :alt="featuredProduct.name"
               decoding="async"
            />
            <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent"></div>

            <div class="absolute inset-x-5 bottom-5 md:inset-x-8 md:bottom-7 flex items-end justify-between gap-4">
               <div class="min-w-0">
                  <span v-if="featuredProduct.inventoryCount === 0" class="inline-flex h-7 px-2.5 mb-2.5 rounded-full bg-white text-text-main text-[12px] font-semibold items-center">
                     {{ lang === 'cn' ? '已售罄' : 'Sold out' }}
                  </span>
                  <span v-else class="inline-flex h-7 px-2.5 mb-2.5 rounded-full bg-white/95 text-secondary-content text-[12px] font-semibold items-center gap-1">
                     <AppIcon name="star" weight="fill" class="text-secondary text-sm" />
                     {{ t.bestSeller }}
                  </span>
                  <h2 class="font-display text-[28px] md:text-[40px] font-bold text-white leading-tight tracking-tight line-clamp-2">{{ lang === 'cn' ? featuredProduct.nameCN : featuredProduct.name }}</h2>
                  <p class="mt-1 text-white/85 text-sm md:text-base line-clamp-1 md:line-clamp-2 max-w-md">{{ lang === 'cn' ? featuredProduct.descriptionCN : featuredProduct.description }}</p>
               </div>

               <!-- Quick Add Button -->
               <button
                  v-if="featuredProduct.inventoryCount !== 0"
                  type="button"
                  :aria-label="t.addToCart"
                  class="size-12 md:size-14 rounded-full bg-white text-primary flex items-center justify-center shadow-float shrink-0"
               >
                  <AppIcon name="plus" weight="bold" class="text-xl md:text-2xl" />
               </button>
            </div>
         </div>

         <!-- Trending Section -->
         <section class="lg:col-span-2 animate-fade-in" style="animation-delay: 120ms">
            <div class="flex items-center justify-between mb-3">
               <h2 class="font-display text-xl md:text-2xl font-bold tracking-tight text-text-main">{{ t.trendingNow }}</h2>
               <button type="button" @click="emit('navigate', 'order')" class="min-h-11 px-3 -mr-3 rounded-full text-primary text-[15px] font-semibold flex items-center gap-1 active:bg-primary-soft">
                  {{ t.seeAll }}
                  <AppIcon name="caret-right" weight="bold" class="text-sm" />
               </button>
            </div>

            <!-- Compact rows on phones and beside the featured card, tiles on iPad portrait -->
            <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-1 gap-3">
               <div
                  v-for="(p, i) in trending"
                  :key="p.id"
                  @click="p.inventoryCount !== 0 && emit('quick-add', p)"
                  data-testid="product-card"
                  class="bg-white p-3 rounded-card shadow-card flex items-center gap-3.5 md:flex-col md:items-stretch md:gap-3 lg:flex-row lg:items-center lg:gap-3.5 cursor-pointer transition-transform duration-150 ease-out active:scale-[0.98] animate-slide-up-content"
                  :class="{'opacity-60 pointer-events-none': p.inventoryCount === 0}"
                  :style="{ animationDelay: `${140 + i * 40}ms` }"
               >
                  <div class="w-16 h-16 md:w-full md:h-auto md:aspect-[4/3] lg:w-[72px] lg:h-[72px] lg:aspect-auto rounded-tile overflow-hidden bg-cream shrink-0">
                     <img :src="p.image" class="w-full h-full object-cover" :class="{'grayscale': p.inventoryCount === 0}" :alt="p.name" loading="lazy" decoding="async" />
                  </div>

                  <div class="min-w-0 flex-1 md:px-1 lg:px-0">
                     <h3 class="text-[15px] md:text-base font-semibold text-text-main leading-snug line-clamp-1">{{ lang === 'cn' ? p.nameCN : p.name }}</h3>
                     <p v-if="p.inventoryCount === 0" class="mt-1 text-[12px] font-semibold text-text-sub">{{ lang === 'cn' ? '已售罄' : 'Sold out' }}</p>
                     <p v-else class="mt-1 text-[15px] font-bold text-text-main tabular-nums"><span class="text-[12px] font-semibold mr-0.5">¥</span>{{ Number(p.price).toFixed(2) }}</p>
                  </div>

                  <span v-if="p.inventoryCount !== 0" class="size-9 rounded-full bg-primary-soft text-primary flex md:hidden lg:flex items-center justify-center shrink-0" aria-hidden="true">
                     <AppIcon name="plus" weight="bold" class="text-base" />
                  </span>
               </div>
            </div>
         </section>
      </div>
    </div>
  </div>
</template>
