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

import AppIcon from '@shared/components/AppIcon.vue';
import { ref, computed } from 'vue';
import { TRANSLATIONS, OPTION_TRANSLATIONS } from '../data';
import type { Product, Language } from '../types';
import { useSheetDrag } from '../composables/useSheetDrag';
import { motionMs } from '@shared/motion';

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

// 下拉关闭: 按住商品图往下拖 (手机抽屉和 iPad 卡片都支持)
const sheetEl = ref<HTMLElement | null>(null);
const backdropEl = ref<HTMLElement | null>(null);
const { handlers: dragHandlers } = useSheetDrag({
  sheet: sheetEl,
  backdrop: backdropEl,
  onDismiss: () => emit('close'),
});

// --- 方法定义 (Methods) ---

/**
 * 处理关闭弹窗
 */
// The exit (--dur-sheet-out, ~65% of the entrance) finishes before unmounting.
const handleClose = () => {
  if (isClosing.value) return;
  isClosing.value = true;
  setTimeout(() => {
    emit('close');
  }, motionMs('--dur-sheet-out', 380));
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
  
  // 动画序列: 按钮内容弹一下变成「已加入」，停留片刻让用户看清，再收起面板
  isJelly.value = true;
  isSuccess.value = true;
  
  setTimeout(() => {
    isJelly.value = false;
  }, motionMs('--dur-spring', 680));
  setTimeout(handleClose, 720);
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
     <!-- Backdrop (tap to close); no blur, which repaints the whole screen every frame the sheet moves -->
     <div
        ref="backdropEl"
        class="absolute inset-0 bg-black/35 transition-opacity duration-sheet-out ease-out"
        :class="isClosing ? 'opacity-0' : 'opacity-100 animate-fade-in'"
        @click="handleClose"
     ></div>

     <!-- Sheet: bottom sheet on phones, centered card on iPad; height follows the content -->
     <div
       ref="sheetEl"
       @click="handleContentClick"
       role="dialog"
       aria-modal="true"
       aria-labelledby="modal-title"
       class="bg-surface-light w-full max-h-[90%] md:max-h-full md:max-w-lg rounded-t-sheet md:rounded-sheet overflow-hidden flex flex-col shadow-sheet md:shadow-float relative z-10 transition-[transform,opacity] duration-sheet-out ease-drawer"
       :class="isClosing ? 'translate-y-full md:translate-y-4 md:scale-[0.97] opacity-0' : 'animate-slide-up-modal md:animate-scale-in'"
     >
        <!-- Close -->
        <button
          type="button"
          @click="handleClose"
          :aria-label="lang === 'cn' ? '关闭' : 'Close'"
          class="absolute top-4 right-4 z-30 size-10 rounded-full bg-white/90 text-text-main flex items-center justify-center"
        >
           <AppIcon name="x" class="text-lg" />
        </button>

        <div class="flex-1 min-h-0 overflow-y-auto no-scrollbar scroll-smooth-touch">
           <!-- Photo (also the drag handle: swipe down to close) -->
           <div class="relative h-[260px] md:h-[320px] w-full shrink-0 overflow-hidden bg-cream touch-none" v-on="dragHandlers">
              <img
                :src="product.image"
                :alt="lang === 'cn' ? product.nameCN : product.name"
                class="w-full h-full object-cover animate-fade-in"
                decoding="async"
              />
              <div class="absolute top-2.5 left-1/2 -translate-x-1/2 h-1 w-9 bg-white/85 rounded-full" aria-hidden="true"></div>
           </div>

           <div class="px-6 md:px-8 pt-6 pb-7 md:pb-8">
              <h1
                id="modal-title"
                class="font-serif text-[28px] md:text-[34px] font-medium leading-tight tracking-[-0.01em] text-text-main animate-slide-up-content"
                style="animation-delay: 80ms"
              >
                {{ lang === 'cn' ? product.nameCN : product.name }}
              </h1>
              <p class="mt-2 text-[15px] text-text-sub leading-relaxed line-clamp-3 animate-slide-up-content" style="animation-delay: 130ms">
                {{ lang === 'cn' ? product.descriptionCN : product.description }}
              </p>

              <!-- Sweetness -->
              <div class="mt-8 animate-slide-up-content" style="animation-delay: 180ms">
                <p class="text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub">{{ t.sweetness }}</p>
                <div class="mt-3 grid grid-cols-4 gap-2">
                   <button
                     v-for="s in (['0%', '50%', 'Regular', '120%'] as const)"
                     :key="s"
                     @click="sugar = s"
                     type="button"
                     :aria-pressed="sugar === s"
                     class="h-11 rounded-full border text-[14px] transition-colors duration-color"
                     :class="sugar === s ? 'bg-primary border-primary text-white font-medium' : 'border-line text-text-main'"
                   >
                      {{ OPTION_TRANSLATIONS.sugar[s][lang] || s }}
                   </button>
                </div>
              </div>
           </div>
        </div>

        <!-- Price & Add -->
        <div class="flex-none px-6 md:px-8 pt-4 pb-[max(env(safe-area-inset-bottom),18px)] md:pb-6 border-t border-line flex items-center gap-5">
           <div class="flex flex-col">
              <span class="text-[12px] text-text-sub">{{ t.total }}</span>
              <span class="text-[22px] font-medium text-text-main tabular-nums leading-tight">¥{{ calculateTotal.toFixed(2) }}</span>
           </div>

           <button
              data-testid="add-to-cart-btn"
              type="button"
              @click="handleAddToCartClick"
              :disabled="isSuccess"
              class="flex-1 h-14 rounded-full text-[16px] font-medium flex items-center justify-center text-white transition-colors duration-color outline-none"
              :class="isSuccess ? 'bg-primary-dark' : 'bg-primary active:bg-primary-dark'"
           >
              <span class="flex items-center gap-2" :class="{ 'animate-jelly': isJelly }">
                <template v-if="isSuccess">
                   <AppIcon name="check" class="text-lg" />
                   {{ lang === 'cn' ? '已加入' : 'Added' }}
                </template>
                <template v-else>
                   <AppIcon name="bag" class="text-lg" />
                   {{ t.addToCart }}
                </template>
              </span>
           </button>
        </div>
     </div>
  </div>
</template>
