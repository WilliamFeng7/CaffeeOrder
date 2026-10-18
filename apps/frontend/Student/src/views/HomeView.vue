<script setup lang="ts">
/**
 * HomeView.vue
 *
 * 首页 (Home): greeting, the order in progress (if any), one featured drink
 * and four popular ones. On an iPad it is exactly one screen in either
 * orientation (no scrolling); on phones it scrolls.
 *
 * Motion (first visit only; the tab is cached): the blocks rise in one after
 * another, photos fade in as they arrive. Nothing loops.
 */

import AppIcon from '@/components/AppIcon.vue';
import { computed, ref, onActivated } from 'vue';
import { TRANSLATIONS, PRODUCTS } from '../data';
import type { Product, Language, Order, TabState, ShopStatus } from '../types';
import { useKeepScroll } from '../composables/useKeepScroll';
import { vImgFade } from '../directives/imgFade';
import { orderStage } from '../utils/orderStage';
import { menuPrice } from '../utils/money';
import PriceTag from '../components/PriceTag.vue';

const props = defineProps<{
  lang: Language;
  userName?: string;  // 问候用
  shopStatus: ShopStatus;
  queueCount: number;
  orders: Order[];
  /** The cart bar sits below the page; reserve its vertical space only when needed. */
  reserveCartBar?: boolean;
}>();

const emit = defineEmits<{
  (e: 'navigate', tab: TabState): void;
  (e: 'quick-add', product: Product, origin?: HTMLElement | null): void; // 打开商品面板 (origin: 图片，用于共享元素过渡)
}>();

const t = computed(() => TRANSLATIONS[props.lang]);
const name = (p: Product) => (props.lang === 'cn' ? p.nameCN : p.name);

// 主推: 第一款推荐且有货的商品；没有推荐就取第一款有货的
const inStock = (p: Product) => !p.soldOut;
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

const isOpen = computed(() => props.shopStatus.open);
const businessHours = computed(() => props.shopStatus.businessHours.map((hours) => `${hours.start}–${hours.end}`).join(' · '));

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
    <!-- iPad: exactly one screen, nothing to scroll. The featured card takes
         whatever height is left; type and spacing follow the screen height
         (clamp + vh), so it fits in Safari and as a home-screen app alike.
         Phones scroll as usual. -->
    <div
      class="home-content mx-auto max-w-5xl flex flex-col px-5 md:px-10 pt-4 md:h-full md:pt-5"
      :class="reserveCartBar ? 'pb-24 md:pb-[84px]' : 'pb-8 md:pb-6'"
    >

      <!-- Wordmark & status -->
      <header class="shrink-0 flex items-center justify-between h-10 animate-fade-in">
        <span class="font-serif text-[19px] font-semibold tracking-tight text-text-main">{{ t.downtownCafe }}</span>
        <div class="flex items-center gap-3">
          <span class="text-[12px] text-text-sub tabular-nums">{{ t.queueNow }} {{ queueCount }} {{ lang === 'cn' ? '单' : (queueCount === 1 ? 'order' : 'orders') }}</span>
          <span v-if="!isOpen" class="chip chip-quiet h-7 px-3 text-[12px]">
            <span class="dot" aria-hidden="true"></span>
            {{ t.closed }}
          </span>
        </div>
      </header>

      <!-- Greeting, and beside it in landscape the order in progress -->
      <div class="shrink-0 mt-6 md:mt-[clamp(12px,2.2vh,24px)] md:landscape:flex md:landscape:items-end md:landscape:justify-between md:landscape:gap-10">
        <section class="min-w-0 animate-slide-up-content" style="animation-delay: 40ms">
          <p class="eyebrow">{{ greeting }} {{ displayName }}</p>
          <h1 class="mt-1.5 font-serif text-[32px] md:text-[clamp(30px,5vh,44px)] font-normal leading-[1.06] tracking-[-0.02em] text-text-main text-balance">{{ t.homeSubtitle }}</h1>
          <p v-if="shopStatus.banner" class="mt-2 text-[13px] text-text-sub line-clamp-1">{{ shopStatus.banner }}</p>
          <p v-if="!isOpen" class="mt-1 text-[13px] text-text-sub">{{ t.businessHours }} · {{ businessHours }}</p>
        </section>

        <!-- The order in progress: number, stage, and a bar that grows with it -->
        <button
          v-if="activeOrder && stage"
          type="button"
          @click="emit('navigate', 'pickup')"
          data-testid="home-order"
          class="mt-5 md:landscape:mt-0 w-full md:landscape:w-[340px] shrink-0 flex items-center gap-5 rounded-card bg-primary text-white pl-5 pr-4 py-3.5 text-left animate-slide-up-content"
          style="animation-delay: 80ms"
        >
          <span class="shrink-0">
            <span class="block text-[12px] font-medium text-white/70">{{ t.pickupNum }}</span>
            <span class="mt-1 block font-serif text-[24px] font-normal leading-none tabular-nums break-all">{{ activeOrder.posOrderNo || t.waitingEntry }}</span>
          </span>
          <span class="flex-1 min-w-0">
            <span class="flex items-baseline justify-between gap-3 text-[15px] font-medium">
              <span v-if="activeOrder.posOrderNo" class="grid overflow-hidden">
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
            <AppIcon name="caret-right" class="text-lg" />
          </span>
        </button>
      </div>

      <!-- Featured: the photo is shown whole (never cut at the top or bottom in
           landscape) and melts into the card - towards the copy beside it in
           landscape, down into the copy below it in portrait and on phones. -->
      <article
        class="home-featured press-card relative mt-6 md:mt-[clamp(14px,2.4vh,28px)] md:flex-1 md:min-h-[200px] flex flex-col md:landscape:flex-row rounded-[28px] overflow-hidden bg-surface-light border border-line cursor-pointer animate-slide-up-content"
        style="animation-delay: 120ms"
        data-testid="featured-card"
        @click="featured && open(featured, featuredImg)"
      >
        <div class="featured-photo relative shrink-0 aspect-[16/10] md:aspect-auto md:flex-1 md:min-h-0 md:landscape:flex-none md:landscape:h-full md:landscape:aspect-[4/3]">
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
        <div class="home-featured-copy relative -mt-6 md:mt-0 flex flex-col px-6 pb-6 md:p-[clamp(20px,3.2vh,32px)] md:portrait:-mt-8 md:portrait:flex-row md:portrait:items-end md:portrait:gap-8 md:landscape:flex-1 md:landscape:min-w-0 md:landscape:justify-center md:landscape:-ml-14 md:landscape:pl-0 md:landscape:pr-[clamp(28px,4vw,56px)]">
          <template v-if="featured">
            <div class="min-w-0 md:portrait:flex-1">
              <p v-if="featured.isPopular" class="flex items-center gap-1.5 text-[13px] font-medium text-secondary-content">
                <AppIcon name="star" weight="regular" class="text-[14px]" />
                {{ t.bestSeller }}
              </p>
              <h2 class="home-featured-name mt-2 font-serif text-[32px] md:text-[clamp(30px,5.4vh,46px)] font-normal leading-[1.04] tracking-[-0.015em] text-text-main">{{ name(featured) }}</h2>
              <p class="mt-2.5 max-w-[44ch] text-[15px] text-text-sub leading-relaxed line-clamp-2 [@media(max-height:760px)]:line-clamp-1 text-balance">{{ lang === 'cn' ? featured.descriptionCN : featured.description }}</p>
            </div>
            <div class="mt-6 md:portrait:mt-0 md:portrait:shrink-0 md:portrait:flex-col md:portrait:items-end md:portrait:gap-3 flex items-center justify-between gap-6">
              <PriceTag :value="featured.price" class="font-serif text-[34px] md:text-[clamp(30px,4.6vh,40px)] text-text-main" />
              <button type="button" class="btn btn-primary px-6 gap-1.5" @click.stop="open(featured, featuredImg)">
                <AppIcon name="plus" class="text-[17px]" />
                {{ lang === 'cn' ? '加入' : 'Add' }}
              </button>
            </div>
          </template>
        </div>
      </article>

      <!-- Popular: a quiet shelf under the feature. iPad: compact cards with
           the whole photo as a square thumbnail (four across in landscape, two
           by two in portrait); phones: photo cards, two by two. -->
      <section v-if="trending.length" class="home-trending shrink-0 mt-10 md:mt-[clamp(16px,3vh,32px)]">
        <div class="flex items-center justify-between animate-fade-in" style="animation-delay: 160ms">
          <h2 class="font-serif text-[22px] md:text-[clamp(20px,3vh,26px)] font-normal text-text-main">{{ t.trendingNow }}</h2>
          <button type="button" @click="emit('navigate', 'order')" class="h-11 -mr-2 px-2 text-[14px] font-medium text-text-main underline decoration-line-strong decoration-1 underline-offset-[5px]">
            {{ t.fullMenu }}
          </button>
        </div>

        <ul class="mt-2 grid grid-cols-2 gap-x-4 gap-y-6 md:gap-3 md:landscape:grid-cols-4">
          <li
            v-for="(p, i) in trending"
            :key="p.id"
            class="animate-slide-up-content"
            :style="{ animationDelay: `${180 + i * 45}ms` }"
          >
            <button
              type="button"
              class="press-card w-full text-left md:flex md:items-center md:gap-3 md:p-2.5 md:pr-3 md:rounded-[20px] md:bg-surface-light md:border md:border-line"
              data-testid="product-card"
              @click="openCard(p, $event)"
            >
              <span class="relative block aspect-square md:w-[clamp(56px,9vh,84px)] md:shrink-0 rounded-card md:rounded-[14px] overflow-hidden bg-cream">
                <img v-img-fade :src="p.thumb" :data-full="p.image" :alt="name(p)" class="card-photo w-full h-full object-cover" decoding="async" />
                <span class="md:hidden absolute right-2.5 bottom-2.5 size-9 rounded-full bg-white/95 text-text-main shadow-card flex items-center justify-center" aria-hidden="true">
                  <AppIcon name="plus" class="text-[16px]" />
                </span>
              </span>
              <span class="block min-w-0 md:flex-1">
                <span class="mt-2.5 md:mt-0 block text-[15px] font-medium leading-snug text-text-main line-clamp-2">{{ name(p) }}</span>
                <span class="mt-0.5 block text-[14px] text-text-sub tabular-nums">{{ menuPrice(p.price) }}</span>
              </span>
            </button>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
