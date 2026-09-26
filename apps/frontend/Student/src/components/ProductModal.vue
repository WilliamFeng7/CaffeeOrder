<script setup lang="ts">
/**
 * ProductModal.vue
 * 
 * 商品详情/定制弹窗组件 (Product Modal Component).
 * 
 * 主要功能 (Core Features):
 * 1. 商品详情展示 (Product Details): 大图、名称、描述。
 * 2. 规格选择 (Customization):
 *    - 杯型 (Size): Regular / Large (加价) / Small.
 *    - 温度 (Temperature): Hot / Iced.
 *    - 糖度 (Sugar): 0% - 120%.

 * 3. 价格计算 (Dynamic Price): 根据规格(如大杯、加料)实时更新总价。
 * 4. 交互动画 (Animations): 
 *    - 进入/退出动画 (Slide Up/Down).
 *    - 加入购物车反馈动画 (Jelly/Success).
 */

import { ref, computed } from 'vue';
import { TRANSLATIONS, OPTION_TRANSLATIONS } from '../data';
import type { Product, Language } from '../types';

// --- Props & Events ---
const props = defineProps<{
  product: Product; // 当前展示的商品对象
  lang: Language;   // 当前语言环境
}>();

const emit = defineEmits<{
  (e: 'close'): void; // 关闭弹窗
  (e: 'add-to-cart', options: { size: string; temp: string; sugar: string }): void; // 加入购物车
}>();

// --- 状态定义 (State Definitions) ---

// 选中的温度 (默认为热)
const temp = ref('Hot');

// 选中的糖度 (默认为正常糖)
const sugar = ref('Regular');

// 状态: 是否正在执行关闭动画 (用于控制 CSS transition)
const isClosing = ref(false);

// 状态: 是否添加成功 (用于按钮反馈)
const isSuccess = ref(false);

// 状态: 是否触发果冻动画 (按钮点击效果)
const isJelly = ref(false);

// 计算属性: 获取当前语言包
const t = computed(() => TRANSLATIONS[props.lang]);

// --- 方法定义 (Methods) ---

/**
 * 处理关闭弹窗
 */
// Exit runs faster than the entrance (240ms vs 360ms); the unmount waits for it.
const EXIT_MS = 240;

const handleClose = () => {
  if (isClosing.value) return;
  isClosing.value = true;
  setTimeout(() => {
    emit('close');
  }, EXIT_MS);
};

const calculateTotal = computed(() => {
  return props.product.price;
});

/**
 * 处理"加入购物车"点击
 */
const handleAddToCartClick = () => {
  emit('add-to-cart', { 
    size: 'Regular', // Default to Regular internally if needed by TS types, or remove if type updated
    temp: temp.value, 
    sugar: sugar.value
  });
  
  // 动画序列: 按钮弹一下并变成「已添加」，停留片刻让用户看清，再收起面板
  isJelly.value = true;
  isSuccess.value = true;
  
  setTimeout(() => {
    isJelly.value = false;
  }, 300);
  setTimeout(handleClose, 450);
};

/**
 * 阻止冒泡
 * 防止点击弹窗内容区域时触发背景的“关闭”点击事件。
 */
const handleContentClick = (e: MouseEvent) => {
  e.stopPropagation();
};

</script>

<template>
  <div class="fixed inset-0 z-[110] flex items-end md:items-center justify-center md:p-8">
     <!-- Backdrop (Click to close) -->
     <!-- 背景遮罩 (点击空白处关闭)；不做模糊：面板滑动时每一帧都要重算整屏模糊 -->
     <div 
        class="absolute inset-0 bg-black/45 transition-opacity duration-200 ease-out" 
        :class="isClosing ? 'opacity-0' : 'opacity-100 animate-fade-in'"
        @click="handleClose"
     ></div>
     
     <!-- Modal Sheet Panel -->
     <!-- 弹窗主体面板：手机为底部抽屉，iPad 为居中卡片；高度随内容，不再留一大片空白 -->
     <div
       @click="handleContentClick"
       role="dialog"
       aria-modal="true"
       aria-labelledby="modal-title"
       class="bg-background-light w-full max-h-[88%] md:max-h-full md:max-w-2xl rounded-t-[32px] md:rounded-[40px] overflow-hidden flex flex-col shadow-2xl relative z-10 transition-[transform,opacity] duration-200 ease-out"
       :class="isClosing ? 'translate-y-full md:translate-y-6 md:scale-95 opacity-0' : 'animate-slide-up-modal md:animate-scale-in'"
     >
        <!-- Close Button (Floating) -->
        <button
          type="button"
          @click="handleClose"
          :aria-label="lang === 'cn' ? '关闭' : 'Close'"
          class="absolute top-4 right-4 z-30 size-11 rounded-full bg-white/80 backdrop-blur-lg flex items-center justify-center border border-white/60 shadow-sm active:bg-white"
        >
           <span class="material-symbols-rounded text-2xl text-gray-800" aria-hidden="true">close</span>
        </button>

        <!-- Scrollable Content Area -->
        <div class="flex-1 min-h-0 overflow-y-auto no-scrollbar scroll-smooth-touch">
           <!-- Product Image Header -->
           <div class="relative h-[200px] md:h-[280px] w-full shrink-0 overflow-hidden bg-[#F2F2F2]">
              <img
                :src="product.image"
                :alt="lang === 'cn' ? product.nameCN : product.name"
                class="w-full h-full object-cover animate-blur-in"
              />
              <!-- Swipe Indicator (Mobile) -->
              <div class="md:hidden absolute top-2.5 left-1/2 -translate-x-1/2 h-1.5 w-12 bg-white/80 rounded-full shadow-sm" aria-hidden="true"></div>
              <!-- Soft fade into the sheet -->
              <div class="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-background-light to-transparent"></div>
           </div>

           <!-- Title & Description: on the sheet itself, not over the photo -->
           <div class="px-6 md:px-10 -mt-2 relative">
              <h1
                id="modal-title"
                class="text-3xl md:text-5xl font-sans font-black text-[#103E32] tracking-tighter leading-none animate-slide-up-content"
                style="animation-delay: 60ms"
              >
                {{ lang === 'cn' ? product.nameCN : product.name }}
              </h1>
              <p class="text-text-sub font-medium text-sm md:text-base line-clamp-3 max-w-lg leading-relaxed mt-2 animate-slide-up-content" style="animation-delay: 90ms">
                {{ lang === 'cn' ? product.descriptionCN : product.description }}
              </p>
           </div>

           <!-- Options Selection Section -->
           <div class="px-6 md:px-10 pt-6 pb-6 md:pb-8 space-y-6">
               <!-- Sugar Level Selection -->
               <div class="space-y-3 animate-slide-up-content" style="animation-delay: 120ms">
                <label class="text-xs font-black text-text-sub uppercase tracking-widest ml-1">{{ t.sweetness }}</label>
                <div class="flex bg-gray-100/70 p-1.5 rounded-[22px] gap-1.5 border border-gray-100 overflow-x-auto no-scrollbar">
                   <button
                     v-for="s in (['0%', '50%', 'Regular', '120%'] as const)"
                     :key="s"
                     @click="sugar = s"
                     type="button"
                     :aria-pressed="sugar === s"
                     class="flex-1 py-3.5 px-3 min-w-[70px] rounded-2xl text-xs md:text-sm font-bold transition-[background-color,color,box-shadow] duration-150 ease-out"
                     :class="sugar === s ? 'bg-white text-primary shadow-md' : 'text-text-sub active:bg-white/60'"
                   >
                      {{ OPTION_TRANSLATIONS.sugar[s][lang] || s }}
                   </button>
                </div>
              </div>
           </div>
        </div>

        <!-- Sticky Footer: Total & Add Button -->
        <div class="flex-none px-5 md:px-8 pt-3 pb-[max(env(safe-area-inset-bottom),16px)] md:pb-6 bg-white border-t border-gray-50 shadow-[0_-10px_60px_rgba(0,0,0,0.04)] z-20">
           <div class="flex items-center gap-6">
              
              <!-- Total Price Display -->
              <div class="flex flex-col">
                 <span class="text-[10px] font-black text-text-sub tracking-widest uppercase mb-1">{{ t.total }}</span>
                 <span class="text-3xl font-[900] text-primary tracking-tighter leading-none tabular-nums">¥{{ calculateTotal.toFixed(2) }}</span>
              </div>

              <!-- Action Button -->
              <button 
                 data-testid="add-to-cart-btn"
                 type="button"
                 @click="handleAddToCartClick"
                 :disabled="isSuccess"
                 class="flex-1 h-[56px] md:h-[64px] rounded-[28px] md:rounded-[32px] font-sans font-black text-lg md:text-xl flex items-center justify-center gap-3 shadow-[0_20px_50px_-10px_rgba(16,62,50,0.4)] outline-none relative overflow-hidden"
                 :class="isSuccess 
                   ? 'bg-green-600 text-white' 
                   : 'bg-[#103E32] text-white'
                 "
              >  
                 <div class="relative flex items-center gap-3" :class="{ 'animate-jelly': isJelly }">
                   <template v-if="isSuccess">
                      <span class="material-symbols-rounded text-2xl animate-scale-up" aria-hidden="true">check_circle</span>
                      {{ lang === 'cn' ? '已添加' : 'Added' }}
                   </template>
                   <template v-else>
                      <span class="material-symbols-rounded text-2xl" aria-hidden="true">shopping_bag</span>
                      {{ t.addToCart }}
                   </template>
                 </div>
              </button>
           </div>
        </div>
     </div>
  </div>
</template>
