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

import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { CATEGORIES, PRODUCTS, TRANSLATIONS } from '../data';
import type { CartItem, Product, Language, Category } from '../types';

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
  <div class="flex flex-col md:flex-row h-full bg-[#F5F7F6] relative z-0">
    
    <!-- Sidebar (Desktop/iPad) -->
    <!-- 左侧导航栏 (仅在大屏显示) -->
    <aside class="hidden md:flex flex-col w-[128px] shrink-0 bg-white/80 backdrop-blur-xl border-r border-white/40 py-6 z-20 items-center h-full shadow-[4px_0_30px_rgba(0,0,0,0.02)] justify-between">
       
       <!-- Brand Logo -->
       <div class="relative group mt-2">
          <div class="size-16 rounded-[24px] bg-gradient-to-br from-primary to-[#0A2921] flex items-center justify-center shadow-lg shadow-primary/20 transition-transform duration-500 ease-luxury group-active:scale-95">
             <span class="material-symbols-rounded text-white text-3xl">local_cafe</span>
          </div>
       </div>

       <!-- Category Icons List -->
       <!-- 分类图标列表，垂直排列 -->
       <div class="flex-1 w-full px-2 flex flex-col items-center gap-4 my-4 overflow-y-auto no-scrollbar scroll-smooth">
          <div v-for="(cat, idx) in CATEGORIES" :key="cat.id" class="animate-slide-up-content shrink-0" :style="{ animationDelay: `${idx * 60}ms` }">
             <button 
               @click="handleCategoryClick(cat.id)"
               data-testid="category-nav"
               class="group relative w-full flex flex-col items-center gap-2 py-2 outline-none"
             >
                <!-- Icon Container with Active State Styles -->
                <div class="
                   relative size-[60px] rounded-[24px] flex items-center justify-center transition-all duration-500 ease-luxury
                   transform-gpu
                "
                :class="activeCategory === cat.id && !searchTerm
                  ? 'bg-primary text-white shadow-[0_15px_30px_-10px_rgba(16,62,50,0.4)] scale-100 rotate-0' 
                  : 'bg-transparent text-gray-300 scale-90'
                ">
                    <span class="
                       material-symbols-rounded text-[28px] transition-all duration-500 ease-luxury
                    "
                    :class="{ 'filled': activeCategory === cat.id && !searchTerm }">
                       {{ cat.icon }}
                    </span>


                </div>
                
                <!-- Category Name -->
                <span class="
                   text-[10px] font-black uppercase tracking-[0.15em] text-center transition-all duration-500 ease-luxury max-w-full truncate px-1
                "
                :class="activeCategory === cat.id && !searchTerm
                  ? 'text-primary opacity-100 translate-y-0' 
                  : 'text-gray-300 opacity-60'
                ">
                   {{ lang === 'cn' ? cat.nameCN : cat.name }}
                </span>
             </button>
          </div>
       </div>

       <!-- Language Switcher -->
       <button 
          @click="emit('toggle-lang')"
          class="mb-2 size-12 rounded-full border border-gray-100 flex items-center justify-center text-[10px] font-black text-gray-400 bg-white shadow-[0_4px_12px_rgba(0,0,0,0.05)] transition-all duration-500 ease-luxury active:scale-90 shrink-0"
       >
          {{ lang === 'en' ? 'EN' : 'CN' }}
       </button>
    </aside>

    <!-- Main Content Area -->
    <!-- 右侧主内容区域 -->
    <div class="flex-1 flex flex-col h-full overflow-hidden relative bg-background-light">
       
       <!-- Mobile Category Header (Horizontal Scroll) -->
       <!-- 移动端分类导航头 -->
       <div class="md:hidden flex overflow-x-auto no-scrollbar p-4 gap-3 bg-white/80 backdrop-blur-md shrink-0 z-20 sticky top-0 border-b border-gray-50">
           <button 
             v-for="cat in CATEGORIES"
             :key="cat.id"
             @click="handleCategoryClick(cat.id)"
             class="
               flex-none px-5 py-2.5 rounded-full flex items-center gap-2 text-xs font-bold shadow-sm transition-all duration-500 ease-luxury active:scale-95 border
             "
             :class="activeCategory === cat.id 
                ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20' 
                : 'bg-gray-50 text-gray-400 border-transparent'
             "
           >
              <span class="material-symbols-rounded text-lg" :class="{ 'filled': activeCategory === cat.id }">{{ cat.icon }}</span>
              <span>{{ lang === 'cn' ? cat.nameCN : cat.name }}</span>
           </button>
       </div>

       <!-- Header & Search Bar -->
       <header class="px-6 md:px-12 pt-4 md:pt-8 shrink-0 animate-slide-down-content z-30">
          <div class="flex items-center justify-between mb-4 md:mb-8">
             <!-- Title Section -->
             <div class="flex flex-col gap-2">
                <h1 class="text-2xl md:text-4xl lg:text-6xl font-sans font-black text-[#103E32] tracking-tighter leading-none">
                   <!-- Dynamic Title: Shows Category Name or 'Search' -->
                   <template v-if="searchTerm">
                      {{ lang === 'cn' ? '搜索结果' : 'Search' }}
                   </template>
                   <template v-else>
                      {{ lang === 'cn' 
                         ? CATEGORIES.find(c => c.id === activeCategory)?.nameCN 
                         : CATEGORIES.find(c => c.id === activeCategory)?.name
                      }}
                   </template>
                </h1>
                <!-- Product Count -->
                <p class="text-xs font-black text-gray-400 uppercase tracking-[0.2em] animate-fade-in flex items-center gap-2 pl-1">
                   <span class="size-2 rounded-full bg-[#DCCA98]"></span>
                   {{ filteredProducts.length }} {{ t.itemsAvailable }}
                </p>
             </div>
             
             <!-- Search Input Container -->
             <div 
               ref="searchContainerRef"
               class="relative group w-40 md:w-72"
             >
                <input 
                   type="text" 
                   v-model="searchTerm"
                   @focus="showSuggestions = true"
                   @input="showSuggestions = true"
                   :placeholder="t.search"
                   class="w-full h-12 md:h-14 pl-12 pr-6 bg-white rounded-full text-sm font-bold outline-none shadow-[0_8px_20px_-8px_rgba(0,0,0,0.05)] border border-transparent focus:border-primary/10 transition-all duration-300 focus:shadow-xl focus:ring-4 focus:ring-primary/5 placeholder:text-gray-300 relative z-20"
                />
                <span class="material-symbols-rounded absolute left-4 top-1/2 -translate-y-1/2 text-gray-300 transition-colors duration-300 group-focus-within:text-primary scale-90 group-focus-within:scale-100 z-20">search</span>

                <!-- Suggestions Dropdown (Autocomplete) -->
                <div 
                   class="absolute top-full left-0 w-full mt-3 bg-white rounded-[24px] shadow-[0_20px_40px_-10px_rgba(0,0,0,0.1)] border border-gray-50 overflow-hidden transition-all duration-300 origin-top z-10"
                   :class="showSuggestions && suggestions.length > 0 ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 -translate-y-2 pointer-events-none'"
                >
                   <div class="px-3 py-2">
                     <p class="text-[9px] font-black text-gray-300 uppercase tracking-widest px-3 py-2">{{ lang === 'cn' ? '建议' : 'Suggestions' }}</p>
                     <button
                       v-for="p in suggestions"
                       :key="p.id"
                       @click="handleSuggestionClick(p)"
                       class="w-full flex items-center gap-3 p-2 rounded-2xl transition-colors duration-200 group/item text-left"
                     >
                        <img :src="p.image" class="size-10 rounded-xl object-cover bg-gray-100 shrink-0" alt="" />
                        <div class="min-w-0">
                           <p class="text-sm font-bold text-text-main truncate transition-colors">
                              {{ lang === 'cn' ? p.nameCN : p.name }}
                           </p>
                           <p class="text-[10px] font-bold text-gray-400">¥{{ Number(p.price).toFixed(2) }}</p>
                        </div>
                     </button>
                   </div>
                </div>
             </div>
          </div>
       </header>

       <!-- Product Grid Main Area -->
       <main class="flex-1 overflow-y-auto p-6 md:p-12 pt-2 pb-40 no-scrollbar">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
             <!-- Product Card -->
             <div 
                v-for="(product, idx) in filteredProducts"
                :key="product.id"
                @click="emit('select-product', product)"
                data-testid="product-card"
                class="group bg-white rounded-[40px] p-4 pb-6 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.02)] transition-all duration-500 ease-luxury active:scale-[0.96] animate-slide-up-content border border-transparent relative transform-gpu overflow-hidden"
                :style="{ animationDelay: `${idx * 60}ms` }"
             >
                <!-- Image Section -->
                <div class="aspect-[4/3] rounded-[32px] overflow-hidden mb-5 relative bg-[#F2F2F2] shadow-inner">
                   <img 
                      :src="product.image" 
                      :alt="product.name" 
                      class="w-full h-full object-cover transition-transform duration-1000 ease-luxury mix-blend-multiply opacity-90" 
                   />
                   
                   <!-- Floating Add Button -->
                   <div class="absolute bottom-3 right-3 size-14 rounded-[20px] bg-white/90 backdrop-blur-md flex items-center justify-center shadow-lg transition-all duration-500 ease-luxury group-hover:bg-[#103E32] group-hover:text-white group-active:scale-90 group-active:bg-[#103E32] group-active:text-white z-10">
                      <span class="material-symbols-rounded text-[#103E32] font-medium group-hover:text-white group-active:text-white transition-all duration-500 ease-luxury text-2xl group-hover:rotate-90">add</span>
                   </div>

                   <!-- Badges -->
                   <div v-if="product.isPopular" class="absolute top-4 left-4 bg-white/90 backdrop-blur text-primary px-3 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest shadow-sm flex items-center gap-1">
                      <span class="material-symbols-rounded text-[10px] filled text-secondary">star</span>
                      {{ t.bestSeller }}
                   </div>
                   
                   <!-- Quantity Counter Badge (if in cart) -->
                   <div v-if="cart.filter(item => item.id === product.id).reduce((sum, i) => sum + i.quantity, 0) > 0" class="absolute top-4 right-4 bg-primary text-white size-8 rounded-full flex items-center justify-center text-xs font-black shadow-[0_4px_12px_rgba(16,62,50,0.3)] animate-scale-in border-2 border-white">
                      {{ cart.filter(item => item.id === product.id).reduce((sum, i) => sum + i.quantity, 0) }}
                   </div>
                </div>

                <!-- Text Content -->
                <div class="px-3">
                   <h3 class="text-lg md:text-xl font-[800] text-text-main leading-tight mb-2 line-clamp-1 transition-colors">
                      {{ lang === 'cn' ? product.nameCN : product.name }}
                   </h3>
                   <p class="text-text-sub text-xs line-clamp-2 mb-4 leading-relaxed opacity-60 font-medium min-h-[2.5em]">
                      {{ lang === 'cn' ? product.descriptionCN : product.description }}
                   </p>
                   
                   <div class="flex items-center justify-between mt-auto">
                      <span class="text-2xl font-[900] text-text-main tracking-tight">¥{{ Number(product.price).toFixed(2) }}</span>
                      <span class="text-[10px] font-black text-gray-300 bg-gray-50 px-3 py-1.5 rounded-full uppercase tracking-widest transition-all duration-300">
                         {{ lang === 'cn' ? '选规格' : 'Customize' }}
                      </span>
                   </div>
                </div>
             </div>
             
             <!-- Spacer for Bottom Navigation -->
             <div class="h-24 w-full col-span-full"></div>
          </div>
       </main>
    </div>
  </div>
</template>
