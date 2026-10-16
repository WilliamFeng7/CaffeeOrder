<script setup lang="ts">
/**
 * MenuView.vue
 *
 * 菜单视图组件 (Menu View Component).
 *
 * 核心功能 (Core Features):
 * 1. 商品分类 (Categories): iPad 左侧文字目录，手机顶部带滑动下划线的文字标签。
 * 2. 商品列表 (Product Grid): 根据分类筛选显示的商品卡片。
 * 3. 搜索功能 (Fuzzy Search): 支持中英文商品名的模糊搜索，带自动补全建议。
 * 4. 购物车角标 (Badges): 在商品卡片上显示已添加数量。
 *
 * Motion: a new category slides in from the side of its tab and its cards
 * cascade in; the title rolls to the new name; the sidebar highlight and the
 * phone underline spring to the selected category. While searching, the
 * cards that still match glide to their new places and the rest shrink away;
 * photos fade in as they load.
 */

import AppIcon from '@/components/AppIcon.vue';
import RollingNumber from '@shared/components/RollingNumber.vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { CATEGORIES, PRODUCTS, TRANSLATIONS } from '../data';
import type { CartItem, Product, Language } from '../types';
import { useKeepScroll } from '../composables/useKeepScroll';
import { useToastStore } from '../stores/toast';
import { vImgFade } from '../directives/imgFade';
import { pinLeaving } from '@shared/list';
import { menuPrice } from '../utils/money';

// 定义 Props (Props Definition)
const props = defineProps<{
  cart: CartItem[]; // 购物车数据，用于计算商品卡片上的已选数量
  lang: Language;   // 当前语言环境
}>();

// 定义 Events (Events Definition)
const emit = defineEmits<{
  (e: 'select-product', product: Product, origin?: HTMLElement | null): void; // 选中商品 (打开详情弹窗; origin 为卡片图片，用于共享元素过渡)
  (e: 'toggle-lang'): void; // 切换语言
}>();

// --- 状态定义 (State Definitions) ---

// 当前激活的分类 ID (默认为第一个分类)
const activeCategory = ref(CATEGORIES[0].id);

// 搜索框输入的关键词
const searchTerm = ref('');

// 是否显示搜索建议下拉框
const showSuggestions = ref(false);

// 搜索容器 DOM引用，用于处理点击外部关闭逻辑
const searchContainerRef = ref<HTMLElement | null>(null);
const searchInputRef = ref<HTMLInputElement | null>(null);

const toast = useToastStore();

// 被点的售罄商品 (晃一下，而不是毫无反应)
const shakingId = ref<string | null>(null);

// 计算属性: 获取当前语言包
const t = computed(() => TRANSLATIONS[props.lang]);

// 从别的标签页回来时停在原来的位置
const { scroller, onScroll } = useKeepScroll();

// 首次进入时卡片依次出现；之后切换分类整块网格一起过渡
const firstPaint = ref(true);

// 新分类从它所在的一侧滑入 (later category: from the right)
const gridDir = ref<'next' | 'prev'>('next');

// 切换分类时整块网格过渡；搜索时每打一个字不重新过渡
const gridKey = computed(() => (searchTerm.value.trim() ? 'search' : activeCategory.value));

const activeCategoryInfo = computed(() => CATEGORIES.find(c => c.id === activeCategory.value));

// 侧栏高亮块的位置 (每个分类固定 56px 高)
const activeIndex = computed(() => Math.max(0, CATEGORIES.findIndex(c => c.id === activeCategory.value)));
const SIDEBAR_ROW = 56;

const pageTitle = computed(() => {
  if (searchTerm.value.trim()) return props.lang === 'cn' ? '搜索结果' : 'Search';
  const cat = activeCategoryInfo.value;
  return (props.lang === 'cn' ? cat?.nameCN : cat?.name) ?? '';
});

const countUnit = computed(() => {
  const n = filteredProducts.value.length;
  return props.lang === 'cn' ? '款' : (n === 1 ? 'item' : 'items');
});

const isSoldOut = (p: Product) => p.inventoryCount === 0;

// 侧栏当前分类 (searching selects none of them)
const isActiveCategory = (id: string) => activeCategory.value === id && !searchTerm.value;

const categoryOptions = computed(() => CATEGORIES.map(c => ({
  value: c.id,
  label: props.lang === 'cn' ? c.nameCN : c.name,
})));

// --- 方法定义 (Methods) ---

/**
 * 模糊搜索算法 (Fuzzy Search Algorithm)
 *
 * 逻辑:
 * 1. 去除所有空格并转小写。
 * 2. 检查是否直接包含 (include)。
 * 3. 检查是否为子序列 (subsequence) - 即字符按顺序出现即可。
 */
const fuzzySearch = (query: string, text: string): boolean => {
  const q = query.toLowerCase().replace(/\s+/g, '');
  const t = text.toLowerCase().replace(/\s+/g, '');

  // 1. 快速路径: 直接包含
  if (t.includes(q)) return true;

  // 2. 子序列匹配 (Fuzzy)
  // e.g. "lt" matches "Latte"
  let i = 0, j = 0;
  while (i < q.length && j < t.length) {
    if (q[i] === t[j]) i++;
    j++;
  }
  return i === q.length;
};

// --- 计算属性 (Computed Properties) ---

/**
 * 过滤后的商品列表 (Filtered Products)
 *
 * 逻辑:
 * 1. 如果有搜索词 -> 全局搜索匹配中英文名。
 * 2. 如果无搜索词 -> 根据 activeCategory 筛选。
 *    - 'top' 分类特殊处理: 显示热门推荐 (Tags包含 'Best Seller' 或指定ID)。
 */
const filteredProducts = computed(() => {
  // 搜索优先
  if (searchTerm.value.trim()) {
    return PRODUCTS.filter(p =>
      fuzzySearch(searchTerm.value, p.name) ||
      fuzzySearch(searchTerm.value, p.nameCN)
    );
  }

  // 分类筛选
  if (activeCategory.value === 'all') return PRODUCTS;

  return activeCategory.value === 'top'
    ? PRODUCTS.filter(p => p.isPopular || p.tags?.includes('Best Seller') || p.id === '1' || p.id === '2')
    : PRODUCTS.filter(p => p.category === activeCategory.value);
});

/**
 * 搜索建议列表 (Search Suggestions)
 * 仅在有输入时生成，最多返回 5 条匹配结果用于下拉展示。
 */
const suggestions = computed(() => {
  if (!searchTerm.value.trim()) return [];
  return PRODUCTS.filter(p =>
    fuzzySearch(searchTerm.value, p.name) || fuzzySearch(searchTerm.value, p.nameCN)
  ).slice(0, 5);
});

/**
 * 每个商品在购物车中的数量 (Quantity per product)
 * 一次遍历算好，卡片角标直接查表，而不是每张卡片各自 filter + reduce 两遍。
 */
const cartCounts = computed(() => {
  const counts = new Map<string, number>();
  for (const item of props.cart) counts.set(item.id, (counts.get(item.id) ?? 0) + item.quantity);
  return counts;
});

// --- 事件监听 (Event Listeners) ---

/**
 * 处理点击外部事件 (Click Outside)
 * 用于当用户点击搜索框以外区域时，自动关闭搜索建议下拉框。
 * pointerdown, not mousedown: iPad Safari only sends mouse events to elements
 * that look clickable, so a tap on empty space never closed the list.
 */
const handleClickOutside = (event: PointerEvent) => {
  if (searchContainerRef.value && !searchContainerRef.value.contains(event.target as Node)) {
    showSuggestions.value = false;
  }
};

onMounted(() => {
  document.addEventListener('pointerdown', handleClickOutside);
  // Cards cascade in on the first visit; later category switches use a quicker cascade.
  window.setTimeout(() => { firstPaint.value = false; }, 700);
});

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleClickOutside);
});

// --- 交互处理 (Interaction Handlers) ---

/**
 * 切换分类
 * 切换时清空搜索词，回归分类浏览模式。
 */
const handleCategoryClick = (id: string) => {
  const from = CATEGORIES.findIndex(c => c.id === activeCategory.value);
  const to = CATEGORIES.findIndex(c => c.id === id);
  gridDir.value = to >= from ? 'next' : 'prev';
  activeCategory.value = id;
  searchTerm.value = '';
  // A new category starts at its first item, not wherever the last one was scrolled to.
  if (scroller.value) scroller.value.scrollTop = 0;
};

const categoryModel = computed({
  get: () => activeCategory.value,
  set: (id: string) => handleCategoryClick(id),
});

/** 打开商品: 把卡片图片一起交出去，详情面板从它长出来 */
const pick = (product: Product, event: MouseEvent) => {
  if (isSoldOut(product)) {
    // A tap that does nothing feels like a miss: say why, and shake the card.
    shakingId.value = null;
    requestAnimationFrame(() => { shakingId.value = product.id; });
    toast.info(props.lang === 'cn' ? `${product.nameCN}已售罄` : `${product.name} is sold out`);
    return;
  }
  const origin = (event.currentTarget as HTMLElement).querySelector('img');
  emit('select-product', product, origin);
};

/** 清空搜索 (a 44px target inside the field; typing it away on a tablet is slow) */
const clearSearch = () => {
  searchTerm.value = '';
  searchInputRef.value?.focus();
};

/**
 * 点击搜索建议项
 * 直接选中该商品 (触发弹窗)。
 */
const handleSuggestionClick = (p: Product) => {
  emit('select-product', p);
  showSuggestions.value = false; // 关闭下拉
};

</script>

<template>
  <div class="flex flex-col md:flex-row h-full bg-background-light relative z-0">

    <!-- Sidebar (iPad): an icon and a name per category; a white highlight springs to the selected one -->
    <aside class="hidden md:flex flex-col w-[184px] shrink-0 border-r border-line h-full">
       <p class="px-7 pt-10 pb-5 eyebrow">{{ lang === 'cn' ? '菜单' : 'Menu' }}</p>
       <nav class="relative flex-1 overflow-y-auto no-scrollbar px-3" :aria-label="lang === 'cn' ? '商品分类' : 'Categories'">
          <span
            class="absolute left-3 right-3 top-0 h-14 rounded-tile bg-surface-light border border-line transition-[transform,opacity] duration-spring ease-spring pointer-events-none"
            :class="searchTerm ? 'opacity-0' : 'opacity-100'"
            :style="{ transform: `translate3d(0, ${activeIndex * SIDEBAR_ROW}px, 0)` }"
            aria-hidden="true"
          ></span>
          <button
            v-for="cat in CATEGORIES"
            :key="cat.id"
            type="button"
            @click="handleCategoryClick(cat.id)"
            data-testid="category-nav"
            :aria-pressed="isActiveCategory(cat.id)"
            class="relative z-10 w-full h-14 px-4 flex items-center gap-3 text-left transition-colors duration-color"
            :class="isActiveCategory(cat.id) ? 'text-text-main' : 'text-text-sub hover:text-text-main'"
          >
             <AppIcon
                :name="cat.icon"
                :weight="isActiveCategory(cat.id) ? 'regular' : 'light'"
                class="text-[20px] shrink-0"
             />
             <span class="text-[15px] leading-tight" :class="isActiveCategory(cat.id) ? 'font-medium' : ''">
                {{ lang === 'cn' ? cat.nameCN : cat.name }}
             </span>
          </button>
       </nav>

       <!-- Language Switcher -->
       <div class="px-5 pb-6 pt-3">
          <button type="button" @click="emit('toggle-lang')" class="btn btn-outline w-full">
             {{ lang === 'en' ? '中文' : 'English' }}
          </button>
       </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0 h-full overflow-hidden">

       <!-- Categories (phone): text tabs with an underline that glides -->
       <div class="md:hidden shrink-0 overflow-x-auto no-scrollbar px-5 pt-3 border-b border-line">
          <SlidingTabs v-model="categoryModel" :options="categoryOptions" :label="lang === 'cn' ? '商品分类' : 'Categories'" />
       </div>

       <!-- Header & Search -->
       <header class="px-5 md:px-10 pt-6 md:pt-10 pb-5 md:pb-8 flex items-end justify-between gap-6 shrink-0 z-30">
          <div class="min-w-0">
             <p class="eyebrow flex items-center gap-1">
                <RollingNumber :value="filteredProducts.length" />
                <span>{{ countUnit }}</span>
             </p>
             <!-- The title rolls to the new category's name -->
             <h1 class="mt-1 grid grid-cols-[minmax(0,1fr)] overflow-hidden py-0.5 font-serif text-[30px] md:text-[42px] font-normal leading-[1.15] tracking-[-0.015em] text-text-main">
                <Transition :name="gridDir === 'next' ? 'roll-up' : 'roll-down'">
                   <span :key="pageTitle" class="col-start-1 row-start-1 truncate">{{ pageTitle }}</span>
                </Transition>
             </h1>
          </div>

          <div ref="searchContainerRef" class="relative w-40 md:w-72 shrink-0">
             <AppIcon name="search" weight="light" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-lg text-text-sub pointer-events-none z-10" />
             <input
                ref="searchInputRef"
                type="text"
                v-model="searchTerm"
                enterkeyhint="search"
                autocomplete="off"
                autocorrect="off"
                autocapitalize="off"
                spellcheck="false"
                @focus="showSuggestions = true"
                @input="showSuggestions = true"
                @keydown.enter="($event.target as HTMLInputElement).blur()"
                :placeholder="t.search"
                class="w-full h-12 pl-10 pr-12 rounded-full bg-cream border border-transparent text-[16px] text-text-main placeholder:text-text-sub outline-none transition-[background-color,border-color] duration-color focus:bg-surface-light focus:border-line-strong"
             />
             <button
                v-if="searchTerm"
                type="button"
                @click="clearSearch"
                :aria-label="lang === 'cn' ? '清除搜索' : 'Clear search'"
                class="absolute right-0 top-0 size-12 flex items-center justify-center text-text-sub"
             >
                <span class="size-6 rounded-full bg-text-sub/15 flex items-center justify-center pop-in">
                   <AppIcon name="x" class="text-[13px]" />
                </span>
             </button>

             <!-- Suggestions -->
             <div
                class="absolute top-full right-0 mt-2 w-full md:w-80 bg-surface-light rounded-card shadow-float border border-line p-1.5 origin-top-right transition-[opacity,transform] duration-popover ease-out z-40"
                :class="showSuggestions && suggestions.length > 0 ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-[0.97] -translate-y-1 pointer-events-none'"
             >
                <button
                  v-for="(p, i) in suggestions"
                  :key="p.id"
                  type="button"
                  @click="handleSuggestionClick(p)"
                  class="suggest-in w-full min-h-[52px] flex items-center gap-3 p-2 rounded-tile text-left hover:bg-cream active:bg-cream"
                  :style="{ animationDelay: `${i * 25}ms` }"
                >
                   <img v-img-fade :src="p.thumb" :data-full="p.image" class="size-10 rounded-[10px] object-cover bg-cream shrink-0" alt="" decoding="async" />
                   <span class="min-w-0 flex-1">
                      <span class="block text-[14px] font-medium text-text-main truncate">{{ lang === 'cn' ? p.nameCN : p.name }}</span>
                      <span class="block text-[13px] text-text-sub tabular-nums">{{ menuPrice(p.price) }}</span>
                   </span>
                </button>
             </div>
          </div>
       </header>

       <!-- Product Grid -->
       <main ref="scroller" @scroll.passive="onScroll" class="flex-1 overflow-y-auto overflow-x-hidden no-scrollbar px-5 md:px-10 pt-1 pb-40">
          <!-- The old grid leaves on top of the new one (positioned against this box) -->
          <div class="relative">
          <Transition :name="`grid-${gridDir}`">
             <TransitionGroup
                :key="gridKey"
                tag="div"
                name="cards"
                class="relative grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-4 md:gap-x-6 gap-y-8 md:gap-y-10"
                :class="{ 'stagger-in': firstPaint }"
                @before-leave="pinLeaving"
             >
                <!-- Product: the photo is the card -->
                <article
                   v-for="(product, i) in filteredProducts"
                   :key="product.id"
                   @click="pick(product, $event)"
                   data-testid="product-card"
                   class="group press-card relative flex flex-col cursor-pointer"
                   :aria-disabled="isSoldOut(product) || undefined"
                >
                   <div class="flex flex-col" :class="{ shake: shakingId === product.id }" @animationend.self="shakingId = null">
                   <div class="relative aspect-square rounded-card overflow-hidden bg-cream">
                      <img
                         v-img-fade
                         :src="product.thumb"
                         :data-full="product.image"
                         :alt="lang === 'cn' ? product.nameCN : product.name"
                         :loading="i < 6 ? 'eager' : 'lazy'"
                         decoding="async"
                         class="card-photo w-full h-full object-cover"
                         :class="{ 'grayscale opacity-60': isSoldOut(product) }"
                      />

                      <span v-if="isSoldOut(product)" class="absolute top-3 left-3 chip bg-white/90 text-text-main">
                         {{ lang === 'cn' ? '已售罄' : 'Sold out' }}
                      </span>

                      <!-- Quantity in cart; the digits roll on every add -->
                      <span
                         v-if="cartCounts.get(product.id)"
                         class="absolute top-3 right-3 min-w-6 h-6 px-1.5 rounded-full bg-text-main text-white text-xs font-semibold flex items-center justify-center leading-none pop-in"
                      ><RollingNumber :value="cartCounts.get(product.id) ?? 0" /></span>
                   </div>

                   <div class="pt-3 min-w-0">
                      <p v-if="product.isPopular && activeCategory !== 'top'" class="mb-1 text-[10px] font-medium uppercase tracking-[0.16em] text-secondary-content">{{ t.bestSeller }}</p>
                      <h3 class="text-[15px] md:text-base font-medium leading-snug line-clamp-2 md:line-clamp-1" :class="isSoldOut(product) ? 'text-text-sub' : 'text-text-main'">
                         {{ lang === 'cn' ? product.nameCN : product.name }}
                      </h3>
                      <p class="mt-1 text-[14px] text-text-sub tabular-nums">{{ menuPrice(product.price) }}</p>
                   </div>
                   </div>
                </article>
             </TransitionGroup>
          </Transition>
          </div>

          <!-- Nothing found -->
          <div v-if="filteredProducts.length === 0" class="py-24 flex flex-col items-center text-text-sub animate-fade-in">
             <AppIcon name="search" weight="light" class="text-[34px] mb-3" />
             <p class="text-[15px]">{{ lang === 'cn' ? '没有找到相关商品' : 'Nothing matches that' }}</p>
          </div>
       </main>
    </div>
  </div>
</template>
