<script setup lang="ts">
/**
 * ProductModal.vue
 *
 * 商品详情面板 (Product sheet): photo, name, description, sweetness, and the
 * add button. A bottom sheet on phones, a centred card on iPad.
 *
 * Motion:
 * - Opened from a card, the photo grows out of the card (shared-element
 *   morph, see composables/morph.ts) while the sheet fades in around it; with
 *   no card to grow from, the sheet slides up / scales in instead.
 * - Swipe the photo down to dismiss (useSheetDrag).
 * - "Add" turns into "Added", then the photo flies into the cart bar.
 * The parent decides how it closes (morph or `leave()`), because only it knows
 * where the photo should go; this component just says why it wants to close.
 */
import AppIcon from '@shared/components/AppIcon.vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
import { ref, computed } from 'vue';
import { TRANSLATIONS, OPTION_TRANSLATIONS } from '../data';
import type { Product, Language, SheetCloseReason } from '../types';
import { useSheetDrag } from '../composables/useSheetDrag';
import { motionMs } from '@shared/motion';

type Sugar = '0%' | '50%' | 'Regular' | '120%';

const props = defineProps<{
  product: Product;
  lang: Language;
  /** The photo is arriving from a card (the sheet fades instead of sliding). */
  hero?: boolean;
}>();

const emit = defineEmits<{
  (e: 'close', reason: SheetCloseReason): void;
  (e: 'add-to-cart', options: { size: string; temp: string; sugar: string }): void;
}>();

// 温度默认热饮 (no temperature picker on this menu)
const temp = ref('Hot');
const sugar = ref<Sugar>('Regular');
const isClosing = ref(false);
const isSuccess = ref(false);
let closeRequested = false;

const t = computed(() => TRANSLATIONS[props.lang]);

const sugarOptions = computed(() => (['0%', '50%', 'Regular', '120%'] as const).map(s => ({
  value: s,
  label: OPTION_TRANSLATIONS.sugar[s][props.lang] || s,
})));

// 下拉关闭: 按住商品图往下拖 (手机抽屉和 iPad 卡片都支持)
const sheetEl = ref<HTMLElement | null>(null);
const backdropEl = ref<HTMLElement | null>(null);
const photo = ref<HTMLImageElement | null>(null);
const { handlers: dragHandlers } = useSheetDrag({
  sheet: sheetEl,
  backdrop: backdropEl,
  onDismiss: () => emit('close', 'dragged'),
});

const requestClose = (reason: SheetCloseReason) => {
  if (closeRequested) return;
  closeRequested = true;
  emit('close', reason);
};

/** The sheet's own exit, for when the photo has nowhere to fly to. */
const leave = () => new Promise<void>((resolve) => {
  isClosing.value = true;
  window.setTimeout(resolve, motionMs('--dur-sheet-out', 380));
});

defineExpose({ photo, leave });

const handleAdd = () => {
  if (isSuccess.value || closeRequested) return;
  emit('add-to-cart', { size: 'Regular', temp: temp.value, sugar: sugar.value });
  // "Added" stays long enough to be read, then the photo leaves for the cart.
  isSuccess.value = true;
  window.setTimeout(() => requestClose('added'), motionMs('--dur-fade', 360) + 160);
};
</script>

<template>
  <div class="fixed inset-0 z-[110] flex items-end md:items-center justify-center md:p-8">
     <!-- Backdrop (tap to close); no blur, which repaints the whole screen every frame the sheet moves -->
     <div
        ref="backdropEl"
        class="absolute inset-0 bg-[rgba(23,28,25,0.32)] transition-opacity duration-sheet-out ease-out"
        :class="isClosing ? 'opacity-0' : 'animate-fade-in'"
        @click="requestClose('dismiss')"
     ></div>

     <!-- Sheet: bottom sheet on phones, centred card on iPad; height follows the content -->
     <div
       ref="sheetEl"
       role="dialog"
       aria-modal="true"
       aria-labelledby="modal-title"
       class="bg-surface-light w-full max-h-[92%] md:max-h-full md:max-w-[520px] rounded-t-sheet md:rounded-sheet overflow-hidden flex flex-col shadow-sheet md:shadow-float relative z-10 transition-[transform,opacity] duration-sheet-out ease-in"
       :class="isClosing
         ? 'translate-y-full md:translate-y-4 md:scale-[0.97] opacity-0'
         : (hero ? 'animate-fade-in' : 'animate-slide-up-modal md:animate-scale-in')"
       @keydown.esc="requestClose('dismiss')"
     >
        <!-- 44px, and inset from the corner so a thumb near the edge still lands on it -->
        <button
          type="button"
          @click="requestClose('dismiss')"
          :aria-label="lang === 'cn' ? '关闭' : 'Close'"
          class="absolute top-3 right-3 z-30 size-11 rounded-full bg-white/90 text-text-main flex items-center justify-center active:bg-white"
        >
           <AppIcon name="x" class="text-[20px]" />
        </button>

        <div class="flex-1 min-h-0 overflow-y-auto no-scrollbar scroll-smooth-touch">
           <!-- Photo (also the drag handle: swipe down to close) -->
           <div class="relative h-[280px] md:h-[340px] w-full shrink-0 overflow-hidden bg-cream touch-none" v-on="dragHandlers">
              <img
                ref="photo"
                :src="product.image"
                :alt="lang === 'cn' ? product.nameCN : product.name"
                class="w-full h-full object-cover"
                :class="{ 'animate-blur-in': !hero }"
                decoding="async"
              />
              <div class="absolute top-2.5 left-1/2 -translate-x-1/2 h-1 w-9 bg-white/80 rounded-full" aria-hidden="true"></div>
           </div>

           <div class="px-6 md:px-8 pt-7 pb-8">
              <p v-if="product.isPopular" class="eyebrow !text-secondary-content animate-slide-up-content" style="animation-delay: 60ms">{{ t.bestSeller }}</p>
              <h1
                id="modal-title"
                class="mt-1.5 font-serif text-[30px] md:text-[34px] font-medium leading-[1.1] tracking-[-0.01em] text-text-main animate-slide-up-content"
                style="animation-delay: 90ms"
              >
                {{ lang === 'cn' ? product.nameCN : product.name }}
              </h1>
              <p class="mt-3 text-[15px] text-text-sub leading-relaxed line-clamp-3 animate-slide-up-content" style="animation-delay: 140ms">
                {{ lang === 'cn' ? product.descriptionCN : product.description }}
              </p>

              <!-- Sweetness -->
              <div class="mt-9 animate-slide-up-content" style="animation-delay: 190ms">
                <p class="eyebrow">{{ t.sweetness }}</p>
                <SlidingTabs
                  v-model="sugar"
                  :options="sugarOptions"
                  variant="segment"
                  size="lg"
                  stretch
                  :label="t.sweetness"
                  class="mt-3 w-full"
                />
              </div>
           </div>
        </div>

        <!-- Price & Add -->
        <div class="flex-none px-6 md:px-8 pt-4 pb-[max(env(safe-area-inset-bottom),18px)] md:pb-6 border-t border-line flex items-center gap-6">
           <div class="flex flex-col">
              <span class="eyebrow">{{ t.total }}</span>
              <span class="mt-1 font-serif text-[24px] font-medium text-text-main tabular-nums leading-none">¥{{ Number(product.price).toFixed(2) }}</span>
           </div>

           <button
              data-testid="add-to-cart-btn"
              type="button"
              @click="handleAdd"
              :aria-disabled="isSuccess"
              class="btn btn-lg flex-1"
              :class="isSuccess ? 'bg-primary-dark text-white' : 'btn-primary'"
           >
              <!-- The label rolls over to "Added" -->
              <span class="relative inline-grid overflow-hidden" aria-live="polite">
                 <Transition name="roll-up">
                    <span v-if="isSuccess" key="done" class="col-start-1 row-start-1 flex items-center gap-2">
                       <!-- the check pops in just after the label rolls over -->
                       <AppIcon name="check" class="text-lg pop-in" style="animation-delay: 120ms" />
                       {{ lang === 'cn' ? '已加入' : 'Added' }}
                    </span>
                    <span v-else key="add" class="col-start-1 row-start-1">{{ t.addToCart }}</span>
                 </Transition>
              </span>
           </button>
        </div>
     </div>
  </div>
</template>
