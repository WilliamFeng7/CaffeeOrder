<script setup lang="ts">
/**
 * HomeView.vue
 *
 * 首页 (Home): greeting, the order in progress (if any), one featured drink
 * and four popular ones. Sized so that on an iPad in landscape the featured
 * drink, its price and its Add button sit above the fold.
 *
 * Motion (first visit only; the tab is cached): the blocks rise in one after
 * another, photos fade in as they arrive. Nothing loops.
 */

import AppIcon from '@/components/AppIcon.vue';
import { computed, ref, onActivated } from 'vue';
import { TRANSLATIONS, PRODUCTS } from '../data';
import type { Product, Language, Order, TabState } from '../types';
import { useKeepScroll } from '../composables/useKeepScroll';
import { vImgFade } from '../directives/imgFade';
import { orderStage } from '../utils/orderStage';

const props = defineProps<{
  lang: Language;
  userName?: string;  // 问候用
  shopOpen?: boolean; // 来自 /shop/status
  orders: Order[];
}>();

const emit = defineEmits<{
  (e: 'navigate', tab: TabState): void;
  (e: 'quick-add', product: Product, origin?: HTMLElement | null): void; // 打开商品面板 (origin: 图片，用于共享元素过渡)
}>();

const t = computed(() => TRANSLATIONS[props.lang]);
const name = (p: Product) => (props.lang === 'cn' ? p.nameCN : p.name);
const price = (p: Product) => `¥${Number(p.price).toFixed(2)}`;

// 主推: 第一款推荐且有货的商品；没有推荐就取第一款有货的
const inStock = (p: Product) => p.inventoryCount !== 0;
const featured = computed(() =>
  PRODUCTS.find(p => p.isPopular && inStock(p)) ?? PRODUCTS.find(inStock) ?? null);

// 热门: 其余推荐商品在前，再补其他有货商品，共四款 (售罄的不上首页)
const trending = computed(() => {
  const pool = PRODUCTS.filter(p => p.id !== featured.value?.id && inStock(p));
  return [...pool.filter(p => p.isPopular), ...pool.filter(p => !p.isPopular)].slice(0, 4);
});

// 进行中的订单: 先显示做好待取的，再是最新的一笔；点一下去取餐页
const STAGE_RANK: Record<string, number> = { ready: 0, processing: 1, created: 2 };
const openOrders = computed(() => props.orders
  .filter(o => o.status === 'active')
  .sort((a, b) => (STAGE_RANK[a.stage] ?? 3) - (STAGE_RANK[b.stage] ?? 3) || Date.parse(b.date) - Date.parse(a.date)));
const activeOrder = computed(() => openOrders.value[0] ?? null);
const stage = computed(() => (activeOrder.value ? orderStage(activeOrder.value, t.value) : null));

// 问候跟随时间；标签页被缓存，所以每次回到首页时刷新
const hour = ref(new Date().getHours());
onActivated(() => { hour.value = new Date().getHours(); });
const greeting = computed(() => {
  if (hour.value < 5 || hour.value >= 18) return t.value.goodEvening;
  if (hour.value < 11) return t.value.goodMorning;
  return t.value.goodAfternoon;
});
const displayName = computed(() => props.userName || 'Otiaer');

const isOpen = computed(() => props.shopOpen !== false);

const { scroller, onScroll } = useKeepScroll();

const featuredImg = ref<HTMLImageElement | null>(null);
const open = (p: Product, origin: Element | null | undefined) => {
  emit('quick-add', p, (origin as HTMLElement | null) ?? null);
};
const openCard = (p: Product, event: MouseEvent) => {
  open(p, (event.currentTarget as HTMLElement).querySelector('img'));
};
</script>

<template>
  <div ref="scroller" @scroll.passive="onScroll" class="h-full overflow-y-auto no-scrollbar bg-background-light">
    <div class="mx-auto max-w-5xl px-5 md:px-10 pt-4 md:pt-7 pb-36">

      <!-- Wordmark & status -->
      <header class="flex items-center justify-between h-11 animate-fade-in">
        <span class="font-serif text-[19px] font-semibold tracking-tight text-text-main">{{ t.downtownCafe }}</span>
        <span class="chip h-7 px-3 text-[12px]" :class="isOpen ? 'chip-accent' : 'chip-quiet'">
          <span class="dot" aria-hidden="true"></span>
          {{ isOpen ? t.open : t.closed }}
        </span>
      </header>

      <!-- Greeting, and beside it in landscape the order in progress -->
      <div class="mt-7 md:mt-9 lg:mt-8 lg:flex lg:items-end lg:justify-between lg:gap-10">
      <section class="min-w-0 animate-slide-up-content" style="animation-delay: 40ms">
        <p class="eyebrow">{{ greeting }} {{ displayName }}</p>
        <h1 class="mt-2 font-serif text-[32px] md:text-[44px] lg:text-[42px] font-medium leading-[1.08] tracking-[-0.02em] text-text-main text-balance">{{ t.homeSubtitle }}</h1>
      </section>

      <!-- The order in progress: number, stage, and a bar that grows with it -->
      <button
        v-if="activeOrder && stage"
        type="button"
        @click="emit('navigate', 'pickup')"
        data-testid="home-order"
        class="group mt-6 lg:mt-0 w-full lg:w-[360px] shrink-0 flex items-center gap-5 md:gap-7 lg:gap-5 rounded-card bg-primary text-white pl-5 pr-4 md:pl-6 md:pr-5 py-4 text-left animate-slide-up-content"
        style="animation-delay: 80ms"
      >
        <span class="shrink-0">
          <span class="block text-[10px] font-medium uppercase tracking-[0.16em] text-white/65">{{ t.pickupNum }}</span>
          <span class="mt-1 block font-serif text-[30px] font-medium leading-none tabular-nums">{{ activeOrder.dailyNumber }}</span>
        </span>
        <span class="flex-1 min-w-0">
          <span class="flex items-baseline justify-between gap-3 text-[15px] font-medium">
            <span class="grid overflow-hidden">
              <Transition name="roll-up">
                <span :key="stage.label" class="col-start-1 row-start-1">{{ stage.label }}</span>
              </Transition>
            </span>
            <span v-if="openOrders.length > 1" class="text-[12px] text-white/65 tabular-nums">+{{ openOrders.length - 1 }}</span>
          </span>
          <span class="mt-2.5 block h-[3px] rounded-full bg-white/20 overflow-hidden">
            <span class="block h-full rounded-full bg-white origin-left transition-transform duration-spring-soft ease-spring-soft" :style="{ transform: `scaleX(${stage.progress})` }"></span>
          </span>
        </span>
        <span class="size-11 -my-1 rounded-full flex items-center justify-center shrink-0" aria-hidden="true">
          <AppIcon name="arrow-right" class="text-lg nudge" />
        </span>
      </button>
      </div>

      <!-- Featured: photo and copy side by side from iPad up -->
      <article
        class="group mt-6 md:mt-8 lg:mt-7 grid md:grid-cols-[1.12fr_1fr] rounded-sheet overflow-hidden bg-surface-light border border-line cursor-pointer animate-slide-up-content"
        style="animation-delay: 120ms"
        data-testid="featured-card"
        @click="featured && open(featured, featuredImg)"
      >
        <div class="relative aspect-[16/10] md:aspect-auto md:min-h-[300px] lg:min-h-[268px] bg-cream overflow-hidden">
          <img
            v-if="featured"
            ref="featuredImg"
            v-img-fade
            :src="featured.image"
            :alt="name(featured)"
            class="card-photo absolute inset-0 w-full h-full object-cover"
            fetchpriority="high"
            decoding="async"
          />
        </div>
        <div class="flex flex-col p-6 md:p-8 min-h-[220px]">
          <template v-if="featured">
            <p v-if="featured.isPopular" class="eyebrow !text-secondary-content">{{ t.bestSeller }}</p>
            <h2 class="mt-2 font-serif text-[30px] md:text-[34px] lg:text-[36px] font-medium leading-[1.08] tracking-[-0.01em] text-text-main">{{ name(featured) }}</h2>
            <p class="mt-3 text-[15px] text-text-sub leading-relaxed line-clamp-3">{{ lang === 'cn' ? featured.descriptionCN : featured.description }}</p>
            <div class="mt-auto pt-6 flex items-center justify-between gap-4">
              <span class="font-serif text-[26px] font-medium text-text-main tabular-nums">{{ price(featured) }}</span>
              <button type="button" class="btn btn-primary px-6 gap-1.5" @click.stop="open(featured, featuredImg)">
                <AppIcon name="plus" class="text-[17px]" />
                {{ lang === 'cn' ? '加入' : 'Add' }}
              </button>
            </div>
          </template>
        </div>
      </article>

      <!-- Popular: four cards in a row from iPad up, two by two on phones -->
      <section v-if="trending.length" class="mt-10 md:mt-12 lg:mt-9">
        <div class="flex items-center justify-between animate-fade-in" style="animation-delay: 160ms">
          <h2 class="font-serif text-[22px] md:text-[26px] font-medium text-text-main">{{ t.trendingNow }}</h2>
          <button type="button" @click="emit('navigate', 'order')" class="group h-11 -mr-2 px-2 flex items-center gap-1 text-[14px] font-medium text-text-main">
            <span class="link">{{ t.seeAll }}</span>
            <AppIcon name="arrow-right" class="text-sm nudge" />
          </button>
        </div>

        <ul class="mt-3 md:mt-4 grid grid-cols-2 sm:grid-cols-4 gap-x-4 md:gap-x-5 gap-y-6">
          <li
            v-for="(p, i) in trending"
            :key="p.id"
            class="animate-slide-up-content"
            :style="{ animationDelay: `${180 + i * 45}ms` }"
          >
            <button type="button" class="group w-full text-left" data-testid="product-card" @click="openCard(p, $event)">
              <span class="relative block aspect-square rounded-card overflow-hidden bg-cream">
                <img v-img-fade :src="p.thumb" :data-full="p.image" :alt="name(p)" class="card-photo w-full h-full object-cover" decoding="async" />
                <span class="absolute right-2.5 bottom-2.5 size-9 rounded-full bg-white/95 text-text-main shadow-card flex items-center justify-center" aria-hidden="true">
                  <AppIcon name="plus" class="text-[16px]" />
                </span>
              </span>
              <span class="mt-3 block text-[15px] font-medium text-text-main truncate">{{ name(p) }}</span>
              <span class="mt-0.5 block text-[14px] text-text-sub tabular-nums">{{ price(p) }}</span>
            </button>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
