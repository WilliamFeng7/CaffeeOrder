<script setup lang="ts">
/**
 * MenuView.vue
 * 
 * 菜单视图组件 (Menu View Component).
 * 
 * 核心功能 (Core Features):
 * 1. 商品分类展示 (Categories): 左侧可滚动侧边栏 (Desktop) 或顶部横向滚动 (Mobile)。
 * 2. 商品列表 (Product Grid): 根据分类筛选显示的商品卡片。
 * 3. 搜索功能 (Fuzzy Search): 支持中英文商品名的模糊搜索，带自动补全建议。
 * 4. 购物车角标 (Badges): 在商品卡片上显示已添加数量。
 */

import AppIcon from '@shared/components/AppIcon.vue';
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { CATEGORIES, PRODUCTS, TRANSLATIONS } from '../data';
import type { CartItem, Product, Language } from '../types';
import { useKeepScroll } from '../composables/useKeepScroll';

// 定义 Props (Props Definition)
const props = defineProps<{
  cart: CartItem[]; // 购物车数据，用于计算商品卡片上的已选数量
  lang: Language;   // 当前语言环境
}>();

// 定义 Events (Events Definition)
const emit = defineEmits<{
  (e: 'select-product', product: Product): void; // 选中商品 (打开详情弹窗)
  (e: 'remove-product-instance', productId: string): void; // 移除商品 (仅作为预留接口)
  (e: 'toggle-lang'): void; // 切换语言
  (e: 'go-checkout'): void; // 跳转结算
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

// 计算属性: 获取当前语言包
const t = computed(() => TRANSLATIONS[props.lang]);

// 从别的标签页回来时停在原来的位置
const { scroller, onScroll } = useKeepScroll();

// 首次进入时卡片依次出现；之后切换分类只做淡入淡出
const firstPaint = ref(true);

// 切换分类时整块网格淡入淡出；搜索时每打一个字不重新淡入
const gridKey = computed(() => (searchTerm.value.trim() ? 'search' : activeCategory.value));

const activeCategoryInfo = computed(() => CATEGORIES.find(c => c.id === activeCategory.value));

// 侧栏指示条的位置 (每个分类固定 80px 高，含间距)
const activeIndex = computed(() => Math.max(0, CATEGORIES.findIndex(c => c.id === activeCategory.value)));

const pageTitle = computed(() => {
  if (searchTerm.value.trim()) return props.lang === 'cn' ? '搜索结果' : 'Search';
  const cat = activeCategoryInfo.value;
  return props.lang === 'cn' ? cat?.nameCN : cat?.name;
});

const countLabel = computed(() => {
  const n = filteredProducts.value.length;
  return props.lang === 'cn' ? `${n} 款` : `${n} ${n === 1 ? 'item' : 'items'}`;
});

const isSoldOut = (p: Product) => p.inventoryCount === 0;

// --- 方法定义 (Methods) ---

/**
 * 模糊搜索算法 (Fuzzy Search Algorithm)
 * 
 * 逻辑:
 * 1. 去除所有空格并转小写。
 * 2. 检查是否直接包含 (include)。
 * 3. 检查是否为子序列 (subsequence) - 即字符按顺序出现即可。
 * 
 * @param query 用户输入的搜索词
 * @param text 被搜索的目标文本 (商品名)
 * @returns boolean 是否匹配
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
 * 
 * 逻辑:
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
 */
const handleClickOutside = (event: MouseEvent) => {
  if (searchContainerRef.value && !searchContainerRef.value.contains(event.target as Node)) {
    showSuggestions.value = false;
  }
};

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside);
  // Cards cascade in on the first visit only; switching category just crossfades.
  window.setTimeout(() => { firstPaint.value = false; }, 600);
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside);
});

// --- 交互处理 (Interaction Handlers) ---

/**
 * 切换分类
 * 切换时清空搜索词，回归分类浏览模式。
 */
const handleCategoryClick = (id: string) => {
  activeCategory.value = id;
  searchTerm.value = '';
  // A new category starts at its first item, not wherever the last one was scrolled to.
  if (scroller.value) scroller.value.scrollTop = 0;
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

    <!-- Sidebar (iPad): quiet list; a thin green bar springs to the selected category -->
    <aside class="hidden md:flex flex-col w-[104px] shrink-0 bg-surface-light border-r border-line h-full">
       <nav class="relative flex-1 overflow-y-auto no-scrollbar py-4 flex flex-col gap-1" :aria-label="lang === 'cn' ? '商品分类' : 'Categories'">
          <span
            class="absolute left-0 top-[38px] h-8 w-[3px] rounded-r-full bg-primary transition-[transform,opacity] duration-spring ease-spring pointer-events-none"
            :class="searchTerm ? 'opacity-0' : 'opacity-100'"
            :style="{ transform: `translateY(${activeIndex * 80}px)` }"
            aria-hidden="true"
          ></span>
          <button
            v-for="cat in CATEGORIES"
            :key="cat.id"
            type="button"
            @click="handleCategoryClick(cat.id)"
            data-testid="category-nav"
            :aria-pressed="activeCategory === cat.id && !searchTerm"
            class="flex flex-col items-center justify-center gap-1.5 h-[76px] px-1 transition-colors duration-color"
            :class="activeCategory === cat.id && !searchTerm ? 'text-text-main' : 'text-text-sub active:text-text-main'"
          >
             <AppIcon
               :name="cat.icon"
               :weight="activeCategory === cat.id && !searchTerm ? 'fill' : 'regular'"
               class="text-2xl transition-colors duration-color"
               :class="activeCategory === cat.id && !searchTerm ? 'text-primary' : ''"
             />
             <span class="text-[12px] leading-tight text-center" :class="activeCategory === cat.id && !searchTerm ? 'font-semibold' : 'font-medium'">
                {{ lang === 'cn' ? cat.nameCN : cat.name }}
             </span>
          </button>
       </nav>

       <!-- Language Switcher -->
       <div class="px-3 pb-4 pt-2">
          <button
            type="button"
            @click="emit('toggle-lang')"
            class="w-full h-10 rounded-full border border-line text-text-sub text-[13px] font-medium flex items-center justify-center gap-1.5 active:text-text-main"
          >
             <AppIcon name="translate" class="text-base" />
             {{ lang === 'en' ? '中文' : 'EN' }}
          </button>
       </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0 h-full overflow-hidden">

       <!-- Categories (phone): one scrollable row of chips -->
       <div class="md:hidden flex overflow-x-auto no-scrollbar px-5 pt-4 pb-1 gap-2 shrink-0">
           <button
             v-for="cat in CATEGORIES"
             :key="cat.id"
             type="button"
             @click="handleCategoryClick(cat.id)"
             :aria-pressed="activeCategory === cat.id && !searchTerm"
             class="flex-none h-10 px-4 rounded-full flex items-center gap-1.5 text-[14px] border transition-colors duration-color"
             :class="activeCategory === cat.id && !searchTerm
                ? 'bg-primary border-primary text-white font-medium'
                : 'bg-transparent border-line text-text-sub'"
           >
              <AppIcon :name="cat.icon" :weight="activeCategory === cat.id && !searchTerm ? 'fill' : 'regular'" class="text-base" />
              {{ lang === 'cn' ? cat.nameCN : cat.name }}
           </button>
       </div>

       <!-- Header & Search -->
       <header class="px-5 md:px-10 pt-5 md:pt-9 pb-5 md:pb-7 flex items-end justify-between gap-6 shrink-0 z-30">
          <div class="min-w-0">
             <p class="text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub">{{ countLabel }}</p>
             <h1 class="mt-1 font-serif text-[30px] md:text-[40px] font-medium leading-tight tracking-[-0.01em] text-text-main truncate">{{ pageTitle }}</h1>
          </div>

          <div ref="searchContainerRef" class="relative w-40 md:w-72 shrink-0">
             <AppIcon name="search" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-lg text-text-sub pointer-events-none z-10" />
             <input
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
                class="w-full h-11 pl-10 pr-4 rounded-full bg-cream border border-transparent text-[15px] text-text-main placeholder:text-text-sub outline-none transition-[background-color,border-color] duration-color focus:bg-surface-light focus:border-line"
             />

             <!-- Suggestions -->
             <div
                class="absolute top-full right-0 mt-2 w-full md:w-80 bg-surface-light rounded-card shadow-float border border-line p-1.5 origin-top-right transition-[opacity,transform] duration-popover ease-out z-40"
                :class="showSuggestions && suggestions.length > 0 ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-[0.97] -translate-y-1 pointer-events-none'"
             >
                <button
                  v-for="p in suggestions"
                  :key="p.id"
                  type="button"
                  @click="handleSuggestionClick(p)"
                  class="w-full min-h-[52px] flex items-center gap-3 p-2 rounded-tile text-left active:bg-cream"
                >
                   <img :src="p.image" class="size-10 rounded-[10px] object-cover bg-cream shrink-0" alt="" decoding="async" />
                   <span class="min-w-0 flex-1">
                      <span class="block text-[14px] font-medium text-text-main truncate">{{ lang === 'cn' ? p.nameCN : p.name }}</span>
                      <span class="block text-[13px] text-text-sub tabular-nums">¥{{ Number(p.price).toFixed(2) }}</span>
                   </span>
                </button>
             </div>
          </div>
       </header>

       <!-- Product Grid -->
       <main ref="scroller" @scroll.passive="onScroll" class="flex-1 overflow-y-auto no-scrollbar px-5 md:px-10 pt-1 pb-40">
          <Transition name="grid-fade" mode="out-in">
             <div :key="gridKey" class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-x-4 md:gap-x-6 gap-y-7 md:gap-y-9" :class="{ 'stagger-in': firstPaint }">
                <!-- Product: the photo is the card -->
                <article
                   v-for="product in filteredProducts"
                   :key="product.id"
                   @click="!isSoldOut(product) && emit('select-product', product)"
                   data-testid="product-card"
                   class="group relative flex flex-col cursor-pointer"
                   :class="{ 'opacity-50 pointer-events-none': isSoldOut(product) }"
                >
                   <div class="relative aspect-square rounded-card overflow-hidden bg-cream transition-transform duration-release ease-out group-active:duration-press group-active:scale-[0.98]">
                      <img
                         :src="product.image"
                         :alt="lang === 'cn' ? product.nameCN : product.name"
                         loading="lazy"
                         decoding="async"
                         class="w-full h-full object-cover"
                         :class="{ 'grayscale': isSoldOut(product) }"
                      />

                      <span v-if="isSoldOut(product)" class="absolute top-3 left-3 h-6 px-2.5 rounded-full bg-text-main/85 text-white text-[11px] font-medium flex items-center">
                         {{ lang === 'cn' ? '已售罄' : 'Sold out' }}
                      </span>
                      <span v-else-if="product.isPopular && activeCategory !== 'top'" class="absolute top-3 left-3 h-6 px-2 rounded-full bg-white/95 text-text-main text-[11px] font-medium flex items-center gap-1">
                         <AppIcon name="star" weight="fill" class="text-secondary text-xs" />
                         {{ t.bestSeller }}
                      </span>

                      <!-- Quantity in cart; keyed by count so it pops on every add -->
                      <span
                         v-if="cartCounts.get(product.id)"
                         :key="cartCounts.get(product.id)"
                         class="absolute top-3 right-3 min-w-6 h-6 px-1.5 rounded-full bg-primary text-white text-xs font-semibold flex items-center justify-center tabular-nums animate-cart-bump"
                      >{{ cartCounts.get(product.id) }}</span>
                   </div>

                   <div class="pt-3 flex items-start justify-between gap-3">
                      <div class="min-w-0">
                         <h3 class="text-[15px] md:text-base font-medium text-text-main leading-snug line-clamp-2 md:line-clamp-1">
                            {{ lang === 'cn' ? product.nameCN : product.name }}
                         </h3>
                         <p class="mt-1 text-[14px] text-text-sub tabular-nums">¥{{ Number(product.price).toFixed(2) }}</p>
                      </div>
                      <span
                         v-if="!isSoldOut(product)"
                         class="mt-0.5 size-9 rounded-full border border-line text-text-main flex items-center justify-center shrink-0 transition-colors duration-color group-active:bg-primary group-active:border-primary group-active:text-white"
                         aria-hidden="true"
                      >
                         <AppIcon name="plus" class="text-base" />
                      </span>
                   </div>
                </article>
             </div>
          </Transition>

          <!-- Nothing found -->
          <div v-if="filteredProducts.length === 0" class="py-24 flex flex-col items-center text-text-sub">
             <AppIcon name="search" class="text-3xl mb-3" />
             <p class="text-[15px]">{{ lang === 'cn' ? '没有找到相关商品' : 'Nothing matches that' }}</p>
          </div>
       </main>
    </div>
  </div>
</template>
