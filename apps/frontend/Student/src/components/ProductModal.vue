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
 * - "Add" rolls over to "Added" with a check; then the sheet leaves as usual
 *   while a small dot hops from the button into the cart (StudentLayout,
 *   composables/cartDot.ts).
 * The parent unmounts it after `leave()` (or at once after a drag-dismiss,
 * when it is already off-screen); this component says why it wants to close.
 *
 * Photo: the card's small photo (already loaded) sits underneath while the
 * full-size one loads and fades in on top, so there is never an empty frame.
 */
import AppIcon from '@/components/AppIcon.vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
import PriceTag from './PriceTag.vue';
import { ref, reactive, computed, onMounted } from 'vue';
import { TRANSLATIONS } from '../data';
import type { Product, Language, SheetCloseReason, ProductSelection, SelectedOption } from '../types';
import { useSheetDrag } from '../composables/useSheetDrag';
import { vImgFade } from '../directives/imgFade';
import { motionMs } from '@shared/motion';
import { menuPrice } from '../utils/money';

const props = defineProps<{
  product: Product;
  lang: Language;
}>();

const emit = defineEmits<{
  (e: 'close', reason: SheetCloseReason): void;
  (e: 'add-to-cart', selection: ProductSelection): void;
}>();

const selected = reactive<Record<number, number>>({});
for (const group of props.product.optionGroups) {
  const initial = group.options.find((option) => option.isDefault) ?? group.options[0];
  if (initial) selected[group.id] = initial.id;
}
const isClosing = ref(false);
// Mounted in its "from" state, then let go on the next style pass, so the
// entrance is a transition (interruptible: closing mid-entrance just turns
// it around) rather than keyframes.
const isEntering = ref(true);
const isSuccess = ref(false);
let closeRequested = false;

const t = computed(() => TRANSLATIONS[props.lang]);

const optionLabel = (option: Product['optionGroups'][number]['options'][number]) => {
  const name = props.lang === 'cn' ? option.name : option.nameEn;
  if (!option.priceDelta) return name;
  const sign = option.priceDelta > 0 ? '+' : '-';
  return `${name} (${sign}${menuPrice(Math.abs(option.priceDelta))})`;
};

const groups = computed(() => props.product.optionGroups.map((group) => ({
  ...group,
  choices: group.options.map((option) => ({ value: option.id, label: optionLabel(option) })),
})));

const chosenOptions = computed<SelectedOption[]>(() => props.product.optionGroups.flatMap((group) => {
  const option = group.options.find((candidate) => candidate.id === selected[group.id]);
  return option ? [{
    id: option.id,
    groupName: group.name,
    groupNameEn: group.nameEn,
    name: option.name,
    nameEn: option.nameEn,
    priceDelta: option.priceDelta,
  }] : [];
}));

const finalPrice = computed(() => props.product.price + chosenOptions.value.reduce((sum, option) => sum + (option.priceDelta ?? 0), 0));

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

// Where the add-to-cart dot sets off from (the parent sends it to the cart).
const addButton = ref<HTMLElement | null>(null);
const addOrigin = () => addButton.value?.getBoundingClientRect() ?? null;

defineExpose({ photo, leave, addOrigin });

onMounted(() => {
  void sheetEl.value?.offsetHeight; // commit the "from" state
  isEntering.value = false;
  // Focus moves into the sheet, so Esc closes it and the page behind it is
  // not where the next Tab lands.
  sheetEl.value?.focus({ preventScroll: true });
});

const handleAdd = () => {
  if (props.product.soldOut || isSuccess.value || closeRequested) return;
  emit('add-to-cart', {
    optionIds: chosenOptions.value.map((option) => option.id!),
    selectedOptions: chosenOptions.value,
    price: finalPrice.value,
  });
  // "Added" stays long enough to be read, then the sheet closes and a small
  // dot drops into the cart (StudentLayout).
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

              <!-- 规格组和选项均来自后端；每组单选。 -->
              <div v-for="group in groups" :key="group.id" class="product-options mt-9">
                <p class="eyebrow">{{ lang === 'cn' ? group.name : group.nameEn }}</p>
                <SlidingTabs
                  v-model="selected[group.id]"
                  :options="group.choices"
                  variant="segment"
                  size="lg"
                  stretch
                  :label="lang === 'cn' ? group.name : group.nameEn"
                  class="mt-3 w-full"
                />
              </div>
           </div>
        </div>

        <!-- Price & Add -->
        <div class="product-actions flex-none px-6 md:px-8 pt-4 pb-[max(env(safe-area-inset-bottom),18px)] md:pb-6 border-t border-line flex items-center gap-6">
           <div class="flex flex-col">
              <span class="eyebrow">{{ t.total }}</span>
              <PriceTag :value="finalPrice" class="mt-1 font-serif text-[30px] text-text-main" />
           </div>

           <button
              ref="addButton"
              data-testid="add-to-cart-btn"
              type="button"
              @click="handleAdd"
              :disabled="product.soldOut || isSuccess"
              :aria-disabled="isSuccess || product.soldOut"
              class="btn btn-lg flex-1"
              :class="isSuccess ? 'bg-primary-dark text-white' : 'btn-primary'"
           >
              <!-- The label rolls over to "Added" -->
              <span class="relative inline-grid overflow-hidden" aria-live="polite">
                 <Transition name="roll-up">
                    <span v-if="product.soldOut" key="sold-out" class="col-start-1 row-start-1">{{ lang === 'cn' ? '售罄' : 'Sold out' }}</span>
                    <span v-else-if="isSuccess" key="done" class="col-start-1 row-start-1 flex items-center gap-2">
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
