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
const handleClose = () => {
  isClosing.value = true;
  setTimeout(() => {
    emit('close');
  }, 600);
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
  
  // 动画序列
  isJelly.value = true;
  isSuccess.value = true;
  
  setTimeout(() => {
    isJelly.value = false;
    // 延迟关闭，让用户看到成功状态
    setTimeout(() => {
      isClosing.value = true;
      setTimeout(() => {
        emit('close');
      }, 500);
    }, 500);
  }, 200);
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
  <div class="fixed inset-0 z-[110] flex items-end justify-center perspective-1000">
     <!-- Backdrop (Click to close) -->
     <!-- 背景遮罩 (点击空白处关闭) -->
     <div 
        class="absolute inset-0 bg-black/40 backdrop-blur-md transition-all duration-600 ease-luxury" 
        :class="isClosing ? 'opacity-0' : 'opacity-100 animate-fade-in'"
        @click="handleClose"
     ></div>
     
     <!-- Modal Sheet Panel -->
     <!-- 弹窗主体面板 -->
     <div 
       @click="handleContentClick"
       class="bg-background-light w-full h-[75%] md:h-[80%] md:max-w-2xl md:rounded-t-[40px] md:mx-auto md:mb-8 md:rounded-b-[40px] rounded-t-[36px] overflow-hidden flex flex-col shadow-2xl relative z-10 transform-gpu transition-all duration-700 ease-luxury"
       :class="isClosing ? 'translate-y-[110%] opacity-0' : 'translate-y-0 animate-slide-up-modal'"
     >
        <!-- Swipe Indicator (Mobile) -->
        <div class="md:hidden flex-none h-1.5 w-12 bg-gray-200/80 rounded-full mx-auto my-3"></div>

        <!-- Close Button (Floating) -->
        <button 
          @click="handleClose" 
          class="absolute top-4 right-4 z-30 size-12 rounded-full bg-white/60 backdrop-blur-lg flex items-center justify-center border border-white/50 shadow-sm transition-all duration-500 ease-luxury active:scale-75 active:rotate-90 active:bg-white"
        >
           <span class="material-symbols-rounded text-2xl text-gray-800">close</span>
        </button>

        <!-- Scrollable Content Area -->
        <div class="flex-1 overflow-y-auto no-scrollbar scroll-smooth-touch pb-4">
           <!-- Product Image Header -->
           <div class="relative h-[180px] md:h-[260px] w-full shrink-0 overflow-hidden">
              <img :src="product.image" class="w-full h-full object-cover animate-blur-in origin-bottom" style="animation-duration: 0.8s" />
              <!-- Gradient Overlay for text readability -->
              <div class="absolute inset-0 bg-gradient-to-t from-background-light via-background-light/20 to-transparent"></div>
              
              <!-- Title & Description -->
              <div class="absolute bottom-0 left-0 right-0 px-8 md:px-12 pb-8">
                 <h1 class="text-4xl md:text-6xl font-sans font-black text-[#103E32] mb-3 tracking-tighter leading-none drop-shadow-sm animate-slide-up-content" style="animation-delay: 100ms">
                   {{ lang === 'cn' ? product.nameCN : product.name }}
                 </h1>
                 <p class="text-text-sub font-medium text-base md:text-lg line-clamp-2 opacity-80 max-w-lg animate-slide-up-content leading-relaxed" style="animation-delay: 200ms">
                   {{ lang === 'cn' ? product.descriptionCN : product.description }}
                 </p>
              </div>
           </div>

           <!-- Options Selection Section -->
           <div class="p-5 md:p-10 space-y-6 md:space-y-10">
               <!-- Size Selection Removed -->
               
               <!-- 2. Sugar Level Selection -->
               <div class="space-y-4 animate-slide-up-content" style="animation-delay: 400ms">
                <label class="text-xs font-black text-gray-400 uppercase tracking-widest ml-1">{{ t.sweetness }}</label>
                <div class="flex bg-gray-100/50 p-2 rounded-[24px] gap-2 border border-gray-100 overflow-x-auto no-scrollbar">
                   <button
                     v-for="s in (['0%', '50%', 'Regular', '120%'] as const)"
                     :key="s"
                     @click="sugar = s"
                     class="flex-1 py-4 px-4 min-w-[70px] rounded-2xl text-xs md:text-sm font-bold transition-all duration-500 active:duration-300 ease-luxury active:scale-90"
                     :class="sugar === s ? 'bg-white text-primary shadow-md scale-100' : 'text-gray-400 active:bg-white/50 scale-95'"
                   >
                      {{ OPTION_TRANSLATIONS.sugar[s][lang] || s }}
                   </button>
                </div>
              </div>


           </div>
        </div>

        <!-- Sticky Footer: Total & Add Button -->
        <div class="flex-none p-4 md:p-8 pt-3 bg-white border-t border-gray-50 pb-[env(safe-area-inset-bottom,16px)] shadow-[0_-10px_60px_rgba(0,0,0,0.04)] z-20">
           <div class="flex items-center gap-6 animate-slide-up-content" style="animation-delay: 500ms">
              
              <!-- Total Price Display -->
              <div class="flex items-center gap-6">
                 <div class="flex flex-col">
                    <span class="text-[10px] font-black text-gray-300 tracking-widest uppercase mb-1">Total</span>
                    <span class="text-3xl font-[900] text-primary tracking-tighter leading-none">¥{{ calculateTotal.toFixed(2) }}</span>
                 </div>
              </div>

              <!-- Action Button -->
              <button 
                 data-testid="add-to-cart-btn"
                 @click="handleAddToCartClick"
                 :disabled="isSuccess"
                 class="flex-1 h-[56px] md:h-[72px] rounded-[28px] md:rounded-[36px] font-sans font-black text-lg md:text-xl flex items-center justify-center gap-3 shadow-[0_20px_50px_-10px_rgba(16,62,50,0.4)] transition-all duration-500 ease-luxury outline-none relative overflow-hidden active:scale-[0.96]"
                 :class="isSuccess 
                   ? 'bg-green-600 text-white scale-100' 
                   : isJelly ? 'animate-jelly bg-[#103E32] text-white' : 'bg-[#103E32] text-white'
                 "
              >  
                 <div class="relative flex items-center gap-3">
                   <template v-if="isSuccess">
                      <span class="material-symbols-rounded text-2xl animate-scale-up">check_circle</span>
                      {{ lang === 'cn' ? '已添加' : 'Added' }}
                   </template>
                   <template v-else>
                      <span class="material-symbols-rounded text-2xl">shopping_bag</span>
                      {{ t.addToCart }}
                   </template>
                 </div>
              </button>
           </div>
        </div>
     </div>
  </div>
</template>
