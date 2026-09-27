<script setup lang="ts">
/**
 * HomeView.vue
 *
 * 首页视图组件 (Home View Component).
 *
 * 主要功能 (Core Features):
 * 1. 欢迎标语 (Welcome): 随时间变化的问候 + 一句标题。
 * 2. 推荐位 (Featured Item): 展示主推商品 (通常是列表中的第2个商品)。
 * 3. 热门推荐 (Trending List): 展示列表中的第3-5个商品，带编号。
 *
 * Motion: the headline is revealed line by line, the featured photo settles
 * from a slight zoom, and the trending rows rise in as they scroll into view.
 */

import AppIcon from '@shared/components/AppIcon.vue';
import { vReveal } from '@shared/reveal';
import { computed, ref, onActivated } from 'vue';
import { TRANSLATIONS, PRODUCTS } from '../data';
import type { Product, Language, TabState } from '../types';
import { useKeepScroll } from '../composables/useKeepScroll';
import { useToastStore } from '../stores/toast';

// 定义组件 Props (Props Definition)
const props = defineProps<{
  lang: Language; // 当前语言环境
  userName?: string; // 当前登录用户名 (用于个性化问候)
  shopOpen?: boolean; // 店铺是否营业 (来自 /shop/status)
}>();

// 定义组件 Events (Events Definition)
const emit = defineEmits<{
  (e: 'navigate', tab: TabState): void; // 导航跳转请求
  (e: 'quick-add', product: Product, origin?: HTMLElement | null): void; // 点击商品 (打开详情弹窗; origin 为图片)
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

const toast = useToastStore();
// 被点的售罄商品晃一下 (a sold-out tap explains itself instead of doing nothing)
const shakingId = ref<string | null>(null);

/** 打开商品，并把被点的图片交给共享元素过渡 */
const open = (p: Product, event: MouseEvent) => {
  if (p.id === 'placeholder') return;
  if (p.inventoryCount === 0) {
    shakingId.value = null;
    requestAnimationFrame(() => { shakingId.value = p.id; });
    toast.info(props.lang === 'cn' ? `${p.nameCN}已售罄` : `${p.name} is sold out`);
    return;
  }
  emit('quick-add', p, (event.currentTarget as HTMLElement).querySelector('img'));
};

</script>

<template>
  <div ref="scroller" @scroll.passive="onScroll" class="flex-1 h-full bg-background-light overflow-y-auto scroll-smooth-touch no-scrollbar pb-32">
    <div class="px-5 md:px-10 pt-6 md:pt-10 max-w-5xl mx-auto">

      <!-- Wordmark & status -->
      <div class="flex items-center justify-between animate-fade-in">
         <span class="font-serif text-[19px] font-semibold tracking-tight text-text-main">{{ t.downtownCafe }}</span>
         <span class="relative flex items-center gap-2 text-[13px] font-medium" :class="isOpen ? 'text-primary' : 'text-text-sub'">
            <span class="relative flex size-1.5">
               <span v-if="isOpen" class="absolute inset-0 rounded-full bg-primary breathe" aria-hidden="true"></span>
               <span class="relative size-1.5 rounded-full" :class="isOpen ? 'bg-primary' : 'bg-text-sub'" aria-hidden="true"></span>
            </span>
            {{ isOpen ? t.open : t.closed }}
         </span>
      </div>

      <!-- Greeting: the headline is revealed from below its own baseline -->
      <header class="mt-12 md:mt-16">
         <p class="eyebrow animate-slide-up-content" style="animation-delay: 60ms">{{ greeting }} {{ displayName }}</p>
         <h1 class="mt-3 font-serif text-[36px] md:text-[56px] font-medium leading-[1.06] tracking-[-0.02em] text-text-main max-w-3xl text-balance animate-text-reveal" style="animation-delay: 120ms">{{ t.homeSubtitle }}</h1>
      </header>

      <!-- Featured + Trending: stacked on phones and iPad portrait, side by side in landscape -->
      <div class="mt-10 md:mt-14 grid gap-12 lg:grid-cols-5 lg:gap-14 lg:items-start">

         <!-- Featured: the photo, then its caption -->
         <article
            class="lg:col-span-3 group cursor-pointer animate-slide-up-content"
            style="animation-delay: 200ms"
            data-testid="featured-card"
            @click="open(featuredProduct, $event)"
         >
            <div class="relative aspect-[4/3] md:aspect-[16/10] rounded-card overflow-hidden bg-cream transition-transform duration-release ease-out group-active:duration-press group-active:scale-[0.99]" :class="{ shake: shakingId === featuredProduct.id }" @animationend.self="shakingId = null">
               <img
                  v-if="featuredProduct.image"
                  :src="featuredProduct.image"
                  class="w-full h-full object-cover hero-settle transition-transform duration-spring-soft ease-out group-hover:scale-[1.03]"
                  :class="{'grayscale': featuredProduct.inventoryCount === 0}"
                  :alt="featuredProduct.name"
                  decoding="async"
               />
               <span v-if="featuredProduct.inventoryCount === 0" class="absolute top-4 left-4 chip bg-white/90 text-text-main">
                  {{ lang === 'cn' ? '已售罄' : 'Sold out' }}
               </span>
            </div>

            <div class="mt-5 flex items-end justify-between gap-6">
               <div class="min-w-0">
                  <p class="eyebrow !text-secondary-content">{{ t.bestSeller }}</p>
                  <h2 class="mt-2 font-serif text-[26px] md:text-[32px] font-medium leading-tight text-text-main">{{ lang === 'cn' ? featuredProduct.nameCN : featuredProduct.name }}</h2>
                  <p class="mt-1.5 text-[15px] text-text-sub leading-relaxed line-clamp-2 max-w-md">{{ lang === 'cn' ? featuredProduct.descriptionCN : featuredProduct.description }}</p>
               </div>
               <div v-if="featuredProduct.inventoryCount !== 0" class="flex flex-col items-end gap-2 shrink-0">
                  <span class="font-serif text-[22px] font-medium text-text-main tabular-nums">¥{{ Number(featuredProduct.price).toFixed(2) }}</span>
                  <span class="link text-[14px] text-primary">
                     {{ t.addToOrder }}
                     <AppIcon name="arrow-right" class="text-sm nudge" />
                  </span>
               </div>
            </div>
         </article>

         <!-- Trending: a numbered hairline list -->
         <section class="lg:col-span-2">
            <div v-reveal="120" class="flex items-baseline justify-between border-b border-line pb-3">
               <h2 class="font-serif text-[22px] md:text-[24px] font-medium text-text-main">{{ t.trendingNow }}</h2>
               <button type="button" @click="emit('navigate', 'order')" class="group min-h-11 -my-3 px-2 -mr-2 text-[14px] font-medium text-text-main flex items-center gap-1">
                  <span class="link">{{ t.seeAll }}</span>
                  <AppIcon name="arrow-right" class="text-sm nudge" />
               </button>
            </div>

            <ul class="divide-y divide-line">
               <li
                  v-for="(p, i) in trending"
                  :key="p.id"
                  v-reveal="160 + i * 70"
                  @click="open(p, $event)"
                  data-testid="product-card"
                  class="group press-row -mx-3 px-3 rounded-tile py-4 flex items-center gap-4 cursor-pointer"
                  :class="{ 'text-text-sub': p.inventoryCount === 0 }"
               >
                  <span class="w-6 font-serif text-[15px] text-text-sub tabular-nums">{{ String(i + 1).padStart(2, '0') }}</span>
                  <div class="size-16 md:size-[72px] rounded-tile overflow-hidden bg-cream shrink-0 transition-transform duration-release ease-out group-active:duration-press group-active:scale-[0.96]" :class="{ shake: shakingId === p.id }" @animationend.self="shakingId = null">
                     <img :src="p.image" class="w-full h-full object-cover" :class="{'grayscale opacity-60': p.inventoryCount === 0}" :alt="p.name" loading="lazy" decoding="async" />
                  </div>
                  <div class="min-w-0 flex-1">
                     <h3 class="text-[15px] md:text-base font-medium text-text-main truncate">{{ lang === 'cn' ? p.nameCN : p.name }}</h3>
                     <p class="mt-1 text-[14px] text-text-sub tabular-nums">
                        <template v-if="p.inventoryCount === 0">{{ lang === 'cn' ? '已售罄' : 'Sold out' }}</template>
                        <template v-else>¥{{ Number(p.price).toFixed(2) }}</template>
                     </p>
                  </div>
                  <AppIcon v-if="p.inventoryCount !== 0" name="arrow-up-right" weight="light" class="text-lg text-text-sub nudge nudge-diag" />
               </li>
            </ul>
         </section>
      </div>
    </div>
  </div>
</template>
