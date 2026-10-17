<script setup lang="ts">
/**
 * ProductModal.vue
 *
 * 商品详情面板 (Product sheet): photo, name, description, sweetness, and the
 * add button. A bottom sheet on phones, a centred card on iPad.
 *
 * Motion (one surface, one movement):
 * - iPad: the card fades in from 97% and a few pixels lower (the modal
 *   recipe, ~260ms on the strong ease-out); phones: the sheet rises from the
 *   bottom edge on the drawer curve. Everything inside moves with it - no
 *   photo flying in from the tapped card, no inner cascade.
 * - The photo settles from a slight zoom as the card arrives.
 * - It leaves the way it came, faster (~200ms).
 * - Swipe the photo down to dismiss (useSheetDrag).
 * - "Add" rolls over to "Added" with a check, then the whole card shrinks
 *   into the cart: it lifts a little, arcs down into the bag icon of the cart
 *   bar while it shrinks, and fades out at the very end (`flyTo`, one WAAPI
 *   animation of transform and opacity on the card itself).
 * The parent unmounts it after `leave()` / `flyTo()` (or at once after a
 * drag-dismiss, when it is already off-screen); this component says why it
 * wants to close.
 *
 * Photo: the card's small photo (already loaded) sits underneath while the
 * full-size one loads and fades in on top, so there is never an empty frame.
 */
import AppIcon from '@/components/AppIcon.vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
import PriceTag from './PriceTag.vue';
import { ref, computed, onMounted } from 'vue';
import { TRANSLATIONS, OPTION_TRANSLATIONS } from '../data';
import type { Product, Language, SheetCloseReason } from '../types';
import { useSheetDrag } from '../composables/useSheetDrag';
import { vImgFade } from '../directives/imgFade';
import { motionMs, cubicBezier, prefersReducedMotion } from '@shared/motion';

type Sugar = '0%' | '50%' | 'Regular' | '120%';

const props = defineProps<{
  product: Product;
  lang: Language;
}>();

const emit = defineEmits<{
  (e: 'close', reason: SheetCloseReason): void;
  (e: 'add-to-cart', options: { size: string; temp: string; sugar: string }): void;
}>();

// 温度默认热饮 (no temperature picker on this menu)
const temp = ref('Hot');
const sugar = ref<Sugar>('Regular');
const isClosing = ref(false);
// Mounted in its "from" state, then let go on the next style pass, so the
// entrance is a transition (interruptible: closing mid-entrance just turns
// it around) rather than keyframes.
const isEntering = ref(true);
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
const photo = ref<HTMLElement | null>(null);
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

/** The sheet's own exit (resolves when it has finished). */
const leave = () => new Promise<void>((resolve) => {
  isClosing.value = true;
  const phone = window.matchMedia('(max-width: 767px)').matches;
  window.setTimeout(resolve, phone ? motionMs('--dur-sheet-out', 280) : motionMs('--dur-modal-out', 200));
});

// 飞进购物车 (Into the cart). The card travels a curved path - a quadratic
// curve through a point above where it starts, so it lifts a touch and then
// drops into the bag - eased off the spot and gliding in, while its size
// holds and then goes quickly. Sampled into keyframes so position and size
// can have their own curves in one compositor-only animation.
const FLIGHT_MS = 640;
const along = cubicBezier(0.45, 0, 0.2, 1);
const shrink = cubicBezier(0.55, 0, 0.75, 0.4);

const flyTo = (target: HTMLElement | null | undefined) => new Promise<void>((resolve) => {
  const sheet = sheetEl.value;
  const to = target?.getBoundingClientRect();
  if (!sheet || !to || !to.width || prefersReducedMotion()) {
    void leave().then(resolve);
    return;
  }
  const from = sheet.getBoundingClientRect();
  const dx = to.left + to.width / 2 - (from.left + from.width / 2);
  const dy = to.top + to.height / 2 - (from.top + from.height / 2);
  const end = Math.max(0.04, (to.width * 1.4) / from.width);
  const cx = dx * 0.25;
  const cy = -Math.min(72, Math.max(24, Math.abs(dy) * 0.2));
  const frames: Keyframe[] = [];
  for (let i = 0; i <= 20; i++) {
    const u = i / 20;
    const t = along(u);
    const x = 2 * (1 - t) * t * cx + t * t * dx;
    const y = 2 * (1 - t) * t * cy + t * t * dy;
    const s = 1 - (1 - end) * shrink(u);
    frames.push({
      offset: u,
      transform: `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0) scale(${s.toFixed(4)})`,
      opacity: u < 0.7 ? 1 : Number((1 - (u - 0.7) / 0.3).toFixed(3)),
    });
  }
  sheet.style.transformOrigin = '50% 50%';
  const flight = sheet.animate(frames, { duration: FLIGHT_MS, easing: 'linear', fill: 'forwards' });
  backdropEl.value?.animate([{ opacity: 1 }, { opacity: 0 }], {
    duration: FLIGHT_MS * 0.8,
    easing: 'cubic-bezier(0.23, 1, 0.32, 1)',
    fill: 'forwards',
  });
  flight.onfinish = () => resolve();
  flight.oncancel = () => resolve();
});

defineExpose({ photo, leave, flyTo });

onMounted(() => {
  void sheetEl.value?.offsetHeight; // commit the "from" state
  isEntering.value = false;
  // Focus moves into the sheet, so Esc closes it and the page behind it is
  // not where the next Tab lands.
  sheetEl.value?.focus({ preventScroll: true });
});

const handleAdd = () => {
  if (isSuccess.value || closeRequested) return;
  emit('add-to-cart', { size: 'Regular', temp: temp.value, sugar: sugar.value });
  // "Added" stays long enough to be read, then the photo leaves for the cart.
  isSuccess.value = true;
  window.setTimeout(() => requestClose('added'), motionMs('--dur-fade', 260) + 120);
};
</script>

<template>
  <div class="product-overlay fixed inset-0 z-[110] flex items-end md:items-center justify-center md:p-8">
     <!-- Backdrop (tap to close); no blur, which repaints the whole screen every frame the sheet moves -->
     <div
        ref="backdropEl"
        class="psheet-backdrop absolute inset-0 bg-[rgba(23,28,25,0.32)]"
        :class="{ 'is-entering': isEntering, 'is-closing': isClosing }"
        @click="requestClose('dismiss')"
     ></div>

     <!-- Sheet: bottom sheet on phones, centred card on iPad; height follows the content -->
     <div
       ref="sheetEl"
       role="dialog"
       aria-modal="true"
       aria-labelledby="modal-title"
       tabindex="-1"
       class="product-sheet psheet outline-none bg-surface-light w-full max-h-[92%] md:max-h-full md:max-w-[520px] rounded-t-sheet md:rounded-sheet overflow-hidden flex flex-col shadow-sheet md:shadow-float relative z-10"
       :class="{ 'is-entering': isEntering, 'is-closing': isClosing }"
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
           <div ref="photo" class="product-photo sheet-photo relative h-[280px] md:h-[340px] w-full shrink-0 overflow-hidden touch-none" v-on="dragHandlers">
              <div class="sheet-photo-media absolute inset-0">
                <img :src="product.thumb" alt="" aria-hidden="true" class="absolute inset-0 w-full h-full object-cover" decoding="async" />
                <img
                  v-img-fade
                  :src="product.image"
                  :alt="lang === 'cn' ? product.nameCN : product.name"
                  class="relative w-full h-full object-cover"
                  decoding="async"
                />
              </div>
              <div class="absolute top-2.5 left-1/2 -translate-x-1/2 h-1 w-9 bg-white/80 rounded-full" aria-hidden="true"></div>
           </div>

           <div class="product-copy px-6 md:px-8 pt-7 pb-8">
              <p v-if="product.isPopular" class="eyebrow !text-secondary-content">{{ t.bestSeller }}</p>
              <h1
                id="modal-title"
                class="mt-1.5 font-serif text-[30px] md:text-[34px] font-normal leading-[1.1] tracking-[-0.01em] text-text-main"
              >
                {{ lang === 'cn' ? product.nameCN : product.name }}
              </h1>
              <p class="mt-3 text-[15px] text-text-sub leading-relaxed line-clamp-3">
                {{ lang === 'cn' ? product.descriptionCN : product.description }}
              </p>

              <!-- Sweetness -->
              <div class="product-options mt-9">
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
        <div class="product-actions flex-none px-6 md:px-8 pt-4 pb-[max(env(safe-area-inset-bottom),18px)] md:pb-6 border-t border-line flex items-center gap-6">
           <div class="flex flex-col">
              <span class="eyebrow">{{ t.total }}</span>
              <PriceTag :value="product.price" class="mt-1 font-serif text-[30px] text-text-main" />
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
                       <!-- the check pops in as the label rolls over -->
                       <AppIcon name="check" weight="fill" class="text-lg pop-in" />
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
