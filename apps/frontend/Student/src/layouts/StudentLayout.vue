<script setup lang="ts">
/**
 * StudentLayout.vue
 * Wrapper for the Student Application logic.
 */
import AppIcon from '@/components/AppIcon.vue';
import AnimatedNumber from '@shared/components/AnimatedNumber.vue';
import RollingNumber from '@shared/components/RollingNumber.vue';
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import MenuView from '../views/MenuView.vue';
import ProductModal from '../components/ProductModal.vue';
import CheckoutView from '../views/CheckoutView.vue';
import PickupView from '../views/PickupView.vue';
import SettingsView from '../views/SettingsView.vue';
import { api } from '../api';
import { CATEGORIES, PRODUCTS, TRANSLATIONS } from '../data';
import { formatCents, sumCents, toCents } from '../utils/money';
import { optionsText } from '../utils/options';
import { useToastStore } from '../stores/toast';
import { type CartItem, type Product, type Order, type Language, type TabState, type UserProfile, type SheetCloseReason, type ProductSelection, type ShopStatus } from '../types';
import { YudaoError } from '@shared/yudao-client';
import { vImgFade } from '../directives/imgFade';
import type { IconName } from '@/icons';
import { motionMs, prefersReducedMotion } from '@shared/motion';
import { useKeyboardInset } from '../composables/useKeyboardInset';
import { dropDot } from '../composables/cartDot';
import { clearPendingCheckout, hasUnscopedPendingCheckout, isDefinitiveNoCharge, loadPendingCheckout, savePendingCheckout } from '../utils/pendingCheckout.js';

const router = useRouter();
const appKeyboardInset = useKeyboardInset(ref(true));

// --- State ---
const currentTab = ref<TabState>('home');
const isCheckoutOpen = ref(false);
const isCartOpen = ref(false);
const cart = ref<CartItem[]>([]);
const pendingCheckout = ref<{ studentNo: string; key: string; items: CartItem[] } | null>(null);
const paymentPending = computed(() => pendingCheckout.value !== null);
const selectedProduct = ref<Product | null>(null);
const language = ref<Language>('en');
const orders = ref<Order[]>([]);
const shopStatus = ref<ShopStatus>({ open: true, banner: '', businessHours: [] });
const shopOpen = computed(() => shopStatus.value.open);
const queueCount = ref(0);
const placing = ref(false);
const toastStore = useToastStore();
const userProfile = ref<UserProfile>({ name: '', studentNo: '', balance: 0 });
let idempotencyKey: string | null = null;
const newIdempotencyKey = () => typeof crypto !== 'undefined' && 'randomUUID' in crypto
  ? crypto.randomUUID()
  : `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;

const t = computed(() => TRANSLATIONS[language.value]);

// 底部标签栏 (Tab bar)
const TABS: { id: TabState; icon: IconName }[] = [
  { id: 'home', icon: 'house' },
  { id: 'order', icon: 'coffee' },
  { id: 'pickup', icon: 'bell' },
  { id: 'profile', icon: 'user' },
];
const tabOrder = (id: TabState) => TABS.findIndex(tab => tab.id === id);
const tabIndex = computed(() => Math.max(0, tabOrder(currentTab.value)));
const tabLabel = (id: TabState) =>
  t.value[`nav${id.charAt(0).toUpperCase() + id.slice(1)}` as keyof typeof t.value] as string;
// 进行中的订单数，显示在「取餐」标签上
const activeOrderCount = computed(() => orders.value.filter(o => o.status === 'active').length);

// 切换标签时新页面从它所在的一侧滑入 (direction follows the tab bar order)
const tabDir = ref<'fwd' | 'back'>('fwd');
watch(currentTab, (next, prev) => {
  tabDir.value = tabOrder(next) >= tabOrder(prev) ? 'fwd' : 'back';
  isCartOpen.value = false;
});

// --- Lifecycle ---
onMounted(() => {
  if (!api.hasToken()) {
    router.push('/login');
    return;
  }

  loadMenuData();
  loadProfile();
  checkShopStatus();
  // Once at start: the Pickup badge and Home's order strip need it before the
  // student ever opens Pickup.
  fetchOrders();
});

const loadProfile = async () => {
  try {
    const profile = await api.getProfile();
    userProfile.value = profile;
    if (pendingCheckout.value && pendingCheckout.value.studentNo !== profile.studentNo) {
      pendingCheckout.value = null;
      idempotencyKey = null;
      cart.value = [];
    }
    if (!pendingCheckout.value) {
      const saved = loadPendingCheckout(profile.studentNo);
      if (saved) {
        pendingCheckout.value = saved;
        idempotencyKey = saved.key;
        cart.value = saved.items;
        isCheckoutOpen.value = true;
      }
    }
  } catch (e) {
    console.error("Failed to load profile", e);
  }
};

const checkShopStatus = async () => {
  try {
    shopStatus.value = await api.getShopStatus();
    if (!shopOpen.value) addToast(language.value === 'cn' ? '店铺已打烊' : 'Shop is currently closed', 'info');
  } catch (e) {
    console.error('Failed to load shop status', e);
  }
};

const loadMenuData = async () => {
  try {
    const menu = await api.getMenu();
    PRODUCTS.splice(0, PRODUCTS.length, ...menu.products);
    CATEGORIES.splice(0, CATEGORIES.length, ...menu.categories);
  } catch (e) {
    console.error("Failed to load menu", e);
  }
};

// --- Methods ---
// Toasts go through the shared store instead of a second, app-local queue.
const addToast = (message: string, type: 'success' | 'info' | 'error' | 'warning' = 'info') => {
  toastStore.addToast(message, type);
};

// --- Product sheet ---------------------------------------------------------
// The sheet animates itself in and out (components/ProductModal.vue). After
// "Add" it leaves as usual while one small dot is tossed from the Add button
// into the bag icon of the cart bar (composables/cartDot.ts), and the bag
// gives a small nod as the dot lands. The sheet is gone well before then.
const productSheet = ref<InstanceType<typeof ProductModal> | null>(null);
const cartBagEl = ref<HTMLElement | null>(null);
const cartBadgeEl = ref<HTMLElement | null>(null);
const cartPillEl = ref<HTMLElement | null>(null);
const cartToggleEl = ref<HTMLButtonElement | null>(null);
let productClosing = false;
// The item counts once the dot has landed in the bag, so the number rolls
// over as it lands. (Held here so a drag-dismiss during "Added" still adds
// it.) The first item goes in at once instead: the cart bar has to rise in
// first, as the place the dot drops into.
const pendingAdd = ref<CartItem | null>(null);

// The bag gives a small nod as the dot lands; its badge pops with the count.
const catchInBag = () => {
  if (prefersReducedMotion()) return;
  cartPillEl.value?.animate([
    { transform: 'translate3d(0, 0, 0) scale(1)' },
    { transform: 'translate3d(0, -1px, 0) scale(1.018)', offset: 0.42 },
    { transform: 'translate3d(0, 0, 0) scale(1)' },
  ], { duration: 320, easing: 'cubic-bezier(0.23, 1, 0.32, 1)' });
  cartBagEl.value?.animate([
    { transform: 'scale(1)', easing: 'cubic-bezier(0.23, 1, 0.32, 1)' },
    { transform: 'scale(1.14)', offset: 0.4, easing: 'cubic-bezier(0.45, 0, 0.25, 1)' },
    { transform: 'scale(1)' },
  ], { duration: 380 });
  cartBadgeEl.value?.animate([
    { transform: 'scale(1)' },
    { transform: 'scale(1.25)', offset: 0.4 },
    { transform: 'scale(1)' },
  ], { duration: 360, delay: 40, easing: 'cubic-bezier(0.23, 1, 0.32, 1)' });
};

const handleSelectProduct = (product: Product) => {
  if (paymentPending.value) {
    addToast(t.value.paymentPending, 'warning');
    return;
  }
  if (selectedProduct.value) return;
  productClosing = false;
  selectedProduct.value = product;
};

const handleCloseProduct = async (reason: SheetCloseReason) => {
  const sheet = productSheet.value;
  if (!sheet || productClosing) return;
  productClosing = true;
  if (reason === 'added') {
    const from = sheet.addOrigin();
    const to = cartBagEl.value?.getBoundingClientRect();
    await Promise.all([sheet.leave(), from && to?.width ? dropDot(from, to) : undefined]);
  } else if (reason !== 'dragged') {
    await sheet.leave(); // dragged: already off-screen
  }
  selectedProduct.value = null;
  if (pendingAdd.value) {
    cart.value = [...cart.value, pendingAdd.value];
    pendingAdd.value = null;
  }
  if (reason === 'added') catchInBag();
};

// 切换语言: the page dips (fast down, softer back up) and the words change
// while it is faint, so the switch reads as one soft change instead of every
// label jumping at once. Opacity only, on two elements; the language control
// itself has already moved its thumb on the tap (SettingsView).
const contentEl = ref<HTMLElement | null>(null);
const navEl = ref<HTMLElement | null>(null);
const LANG_DIP_MS = 340;
let langTimer: number | undefined;
// The language a dip is on its way to (the latest tap wins).
let pendingLang: Language | null = null;
const setLanguage = (target: Language) => {
  if (target === (pendingLang ?? language.value)) return;
  if (prefersReducedMotion()) {
    language.value = target;
    return;
  }
  pendingLang = target;
  window.clearTimeout(langTimer);
  for (const el of [contentEl.value, navEl.value]) {
    el?.animate([
      { opacity: 1, easing: 'cubic-bezier(0.23, 1, 0.32, 1)' },
      { opacity: 0.2, offset: 0.4, easing: 'cubic-bezier(0.25, 0, 0.2, 1)' },
      { opacity: 1 },
    ], { duration: LANG_DIP_MS });
  }
  langTimer = window.setTimeout(() => {
    if (pendingLang) language.value = pendingLang;
    pendingLang = null;
  }, LANG_DIP_MS * 0.4);
};
const handleToggleLang = () => setLanguage((pendingLang ?? language.value) === 'en' ? 'cn' : 'en');

const handleAddToCart = (selection: ProductSelection) => {
  if (paymentPending.value || placing.value) {
    addToast(t.value.paymentPending, 'warning');
    return;
  }
  if (selectedProduct.value) {
    const finalPrice = selection.price;
    idempotencyKey = null;

    const newItem: CartItem = {
      ...selectedProduct.value,
      cartId:
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          // Deprecated String.prototype.substr could hand out colliding ids for
          // two items added in the same tick, which then updated as one row.
          : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
      quantity: 1,
      price: finalPrice,
      optionIds: selection.optionIds,
      selectedOptions: selection.selectedOptions,
    };
    // The student stays where they are: the sheet shows "Added" and closes as
    // a dot drops into the cart bar (on Home and Order), which takes the item
    // as it lands.
    if (cart.value.length === 0) cart.value = [newItem];
    else pendingAdd.value = newItem;
  }
};

const updateCartItemQuantity = (cartId: string, delta: number) => {
  if (paymentPending.value || placing.value) {
    addToast(t.value.paymentPending, 'warning');
    return;
  }
  idempotencyKey = null;
  cart.value = cart.value.map(item => {
    if (item.cartId === cartId) return { ...item, quantity: Math.max(0, item.quantity + delta) };
    return item;
  }).filter(item => item.quantity > 0);
};

const removeCartItem = (cartId: string) => {
  if (paymentPending.value || placing.value) {
    addToast(t.value.paymentPending, 'warning');
    return;
  }
  idempotencyKey = null;
  cart.value = cart.value.filter(item => item.cartId !== cartId);
};

const cartLineTotal = (item: CartItem) => toCents(item.price) * item.quantity;
const cartItemOptions = (item: CartItem) => optionsText(item.selectedOptions, language.value);

const toggleCart = () => {
  if (!cartCount.value) return;
  isCartOpen.value = !isCartOpen.value;
};

const closeCart = (returnFocus = false) => {
  isCartOpen.value = false;
  if (returnFocus) void nextTick(() => cartToggleEl.value?.focus());
};

const openCheckout = () => {
  if (!cartCount.value) return;
  isCartOpen.value = false;
  isCheckoutOpen.value = true;
};

let pollInterval: ReturnType<typeof setInterval> | null = null;
const startPolling = () => {
  if (pollInterval) clearInterval(pollInterval);
  fetchOrders();
  pollInterval = setInterval(fetchOrders, 3000);
};
const stopPolling = () => {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = null;
};

// Never leak the polling interval when the layout unmounts
// (e.g. router-guard redirect on expired token)
onUnmounted(stopPolling);
const orderSignature = (list: Order[]) => list.map(o => `${o.id}:${o.stage}:${o.posOrderNo ?? ''}:${o.aheadCount ?? ''}`).join('|');
// Stage of each order at the previous poll, so an order that turns "ready"
// raises one notice instead of relying on the student watching the card.
let lastStages: Map<string, string> | null = null;
const fetchOrders = async () => {
  try {
     const fetchedOrders = await api.getMyOrders();
     if (currentTab.value === 'home') queueCount.value = await api.getQueue();
     if (lastStages) {
       for (const o of fetchedOrders) {
         const before = lastStages.get(o.id);
         if (o.stage === 'ready' && before && before !== 'ready') {
           addToast(`${t.value.orderReady}${o.posOrderNo ? `：${o.posOrderNo}` : ''}`, 'success');
         }
       }
     }
     lastStages = new Map(fetchedOrders.map(o => [o.id, o.stage]));
     // Most polls bring nothing new: keep the same array then, so the lists
     // (and their FLIP bookkeeping) do not re-render every 3 seconds.
     if (orderSignature(fetchedOrders) !== orderSignature(orders.value)) orders.value = fetchedOrders;
  } catch {
     console.error("Failed to fetch orders");
  }
};

// Poll while the orders are on screen: Pickup, Me, and Home while an order is
// open (its strip follows the order to "ready").
const shouldPoll = (tab: TabState) =>
  tab === 'home' || tab === 'pickup' || tab === 'profile';
watch([currentTab, () => activeOrderCount.value > 0], ([tab], [prevTab]) => {
  if (!shouldPoll(tab)) stopPolling();
  else if (tab !== prevTab || !pollInterval) startPolling();
});

// 下单成功的一瞬 (the order went through): the pay button draws a check
// and holds it for a beat before the sheet slides away to Pickup.
const orderDone = ref(false);
watch(isCheckoutOpen, (open) => {
  if (open) {
    isCartOpen.value = false;
    orderDone.value = false;
  }
});

const handlePlaceOrder = async () => {
  // A second tap while the first request is in flight used to place (and
  // charge) the same cart twice.
  if (placing.value || cart.value.length === 0) return;
  if (!shopOpen.value) {
    addToast(language.value === 'cn' ? '当前不在营业时段，暂不能下单' : 'Ordering is unavailable outside business hours', 'info');
    return;
  }
  if (!userProfile.value.studentNo) {
    addToast(t.value.profileLoading, 'info');
    return;
  }
  if (hasUnscopedPendingCheckout()) {
    addToast(t.value.checkoutRecoveryError, 'error');
    return;
  }
  let attempt = pendingCheckout.value;
  if (!attempt) {
    attempt = {
      studentNo: userProfile.value.studentNo,
      key: idempotencyKey ?? newIdempotencyKey(),
      items: JSON.parse(JSON.stringify(cart.value)) as CartItem[],
    };
    if (!savePendingCheckout(attempt)) {
      idempotencyKey = null;
      addToast(t.value.checkoutStorageError, 'error');
      return;
    }
    pendingCheckout.value = attempt;
  }
  if (attempt.studentNo !== userProfile.value.studentNo) {
    addToast(t.value.paymentPending, 'warning');
    return;
  }
  idempotencyKey = attempt.key;
  placing.value = true;
  try {
    await api.createOrder(attempt.items, attempt.key);
    clearPendingCheckout(attempt.studentNo);
    pendingCheckout.value = null;
    idempotencyKey = null;
    cart.value = [];
    orderDone.value = true;
    const shownAt = performance.now();
    await fetchOrders();
    await loadProfile(); // Refresh balance
    const hold = motionMs('--dur-enter', 560) + 180 - (performance.now() - shownAt);
    if (hold > 0) await new Promise((resolve) => window.setTimeout(resolve, hold));
    isCheckoutOpen.value = false;
    currentTab.value = 'pickup';
    addToast(language.value === 'cn' ? '下单成功!' : 'Order placed successfully!', 'success');
  } catch (e) {
    if (e instanceof YudaoError && isDefinitiveNoCharge(e.code)) {
      clearPendingCheckout(attempt.studentNo);
      pendingCheckout.value = null;
      idempotencyKey = null;
      addToast(e.code === 1080003007 ? t.value.paymentRefunded : e.message, 'info');
    } else {
      idempotencyKey = attempt.key;
      pendingCheckout.value = attempt;
      addToast(e instanceof Error ? e.message : (language.value === 'cn' ? '下单失败，请稍后重试' : 'Order failed'), 'info');
    }
  } finally {
    placing.value = false;
  }
};

// Integer cents, so a multi-item cart cannot drift a cent away from the total
// the server computes (see utils/money.ts).
const cartTotalCents = computed(() => sumCents(cart.value));
const cartCount = computed(() => cart.value.reduce((sum, item) => sum + item.quantity, 0));
const formatTotal = (cents: number) => `¥${formatCents(Math.round(cents))}`;
watch(cartCount, (count) => {
  if (!count) isCartOpen.value = false;
});
</script>

<template>
  <div class="student-shell fixed inset-0 w-full h-full bg-background-light overflow-hidden font-sans text-text-main select-none z-0" :class="{ 'has-cart': cartCount > 0 || !!pendingAdd, 'keyboard-open': appKeyboardInset > 0 }" :style="{ '--app-keyboard-inset': `${appKeyboardInset}px` }">
    <!-- Toasts are rendered once, globally, by <ToastContainer /> in App.vue. -->

    <div class="absolute inset-0 flex flex-col bg-background-light">
    <div ref="contentEl" class="student-content flex-1 min-h-0 overflow-hidden relative w-full h-full z-0">
      <!-- KeepAlive: switching tabs keeps each tab's scroll position, category
           and sub-view; the Transition slides the new tab in from its side.
           The leaving tab is positioned against the inner box (not the padded
           one), so its scroll area keeps its size while it fades out. -->
      <div class="relative h-full">
        <Transition :name="`tab-${tabDir}`">
          <KeepAlive>
            <HomeView v-if="currentTab === 'home'" @navigate="(tab) => currentTab = tab" @quick-add="handleSelectProduct" :lang="language" :user-name="userProfile.name" :shop-status="shopStatus" :queue-count="queueCount" :orders="orders" />
            <MenuView v-else-if="currentTab === 'order'" :cart="cart" @select-product="handleSelectProduct" :lang="language" @toggle-lang="handleToggleLang" />
            <PickupView v-else-if="currentTab === 'pickup'" :orders="orders" :lang="language" :refresh="fetchOrders" @browse="currentTab = 'order'" />
            <SettingsView v-else-if="currentTab === 'profile'" :lang="language" @set-lang="setLanguage" :user-profile="userProfile" :orders="orders" />
          </KeepAlive>
        </Transition>
      </div>
    </div>

    <!-- Cart bar: floats above the tab bar on Home and the menu -->
    <Transition name="cartbar">
      <div v-if="cartCount > 0 && (currentTab === 'order' || currentTab === 'home')" class="student-cart absolute inset-x-0 z-40 flex justify-center px-4 pointer-events-none">
         <div
           v-if="isCartOpen"
           aria-hidden="true"
           class="fixed inset-0 bg-transparent pointer-events-auto"
           @click="closeCart()"
         ></div>

         <div class="relative pointer-events-auto w-full max-w-md">
            <Transition name="cart-panel">
               <section
                  v-if="isCartOpen"
                  id="cart-preview"
                  role="region"
                  :aria-label="t.cart"
                  class="cart-panel absolute bottom-full left-0 right-0 mb-3 rounded-[26px] bg-surface-light border border-line shadow-float overflow-hidden"
                  @keydown.esc.stop="closeCart(true)"
               >
                  <header class="flex items-center gap-3 px-5 pt-4 pb-3 border-b border-line">
                     <div class="min-w-0">
                        <p class="font-serif text-[22px] leading-tight text-text-main">{{ t.cart }}</p>
                        <p class="mt-0.5 text-[12px] text-text-sub tabular-nums">
                           <RollingNumber :value="cartCount" />
                           {{ language === 'cn' ? '件' : (cartCount === 1 ? 'item' : 'items') }}
                        </p>
                     </div>
                     <button
                        type="button"
                        :aria-label="t.closeCart"
                        class="ml-auto size-11 rounded-full flex items-center justify-center text-text-sub active:bg-cream"
                        @click="closeCart(true)"
                     >
                        <AppIcon name="x" class="text-[18px]" />
                     </button>
                  </header>

                  <TransitionGroup tag="div" name="list" class="cart-preview-list relative max-h-[min(42vh,320px)] overflow-y-auto no-scrollbar px-5">
                     <article
                        v-for="item in cart"
                        :key="item.cartId"
                        class="cart-preview-item flex items-center gap-3 py-3 border-b border-line last:border-b-0"
                     >
                        <img
                           v-img-fade
                           :src="item.thumb || item.image"
                           :data-full="item.image"
                           :alt="language === 'cn' ? item.nameCN : item.name"
                           class="size-11 rounded-[12px] object-cover bg-cream shrink-0"
                           decoding="async"
                        />
                        <div class="min-w-0 flex-1">
                           <p class="text-[14px] font-medium text-text-main truncate">{{ language === 'cn' ? item.nameCN : item.name }}</p>
                           <p v-if="cartItemOptions(item)" class="mt-0.5 text-[12px] text-text-sub truncate">{{ cartItemOptions(item) }}</p>
                           <p class="mt-0.5 text-[12px] tabular-nums text-text-sub">
                              <AnimatedNumber :value="cartLineTotal(item)" :format="formatTotal" :from-zero="false" />
                           </p>
                        </div>
                        <div class="cart-preview-actions flex items-center shrink-0">
                           <button
                              type="button"
                              :aria-label="t.decrease"
                              :disabled="paymentPending || placing"
                              class="size-11 rounded-full flex items-center justify-center text-text-main active:bg-cream disabled:opacity-35"
                              @click="updateCartItemQuantity(item.cartId, -1)"
                           >
                              <AppIcon name="minus" class="text-[15px]" />
                           </button>
                           <span class="w-7 text-center text-[15px] font-medium tabular-nums text-text-main">
                              <RollingNumber :value="item.quantity" />
                           </span>
                           <button
                              type="button"
                              :aria-label="t.increase"
                              :disabled="paymentPending || placing"
                              class="size-11 rounded-full flex items-center justify-center text-text-main active:bg-cream disabled:opacity-35"
                              @click="updateCartItemQuantity(item.cartId, 1)"
                           >
                              <AppIcon name="plus" class="text-[15px]" />
                           </button>
                           <button
                              type="button"
                              :aria-label="t.removeItem"
                              :disabled="paymentPending || placing"
                              class="size-11 rounded-full flex items-center justify-center text-text-sub active:bg-danger-soft active:text-danger disabled:opacity-35"
                              @click="removeCartItem(item.cartId)"
                           >
                              <AppIcon name="trash" class="text-[16px]" />
                           </button>
                        </div>
                     </article>
                  </TransitionGroup>

                  <footer class="flex items-center gap-4 px-5 py-4 border-t border-line bg-cream/55">
                     <div class="min-w-0">
                        <p class="eyebrow">{{ t.total }}</p>
                        <AnimatedNumber class="mt-0.5 block font-serif text-[26px] leading-none text-text-main" :value="cartTotalCents" :format="formatTotal" :from-zero="false" />
                     </div>
                     <button type="button" class="ml-auto btn btn-primary btn-lg min-w-[150px]" @click="openCheckout">
                        {{ t.checkout }}
                        <AppIcon name="caret-right" class="text-[16px]" />
                     </button>
                  </footer>
               </section>
            </Transition>

            <div
               ref="cartPillEl"
               class="cart-pill group h-14 rounded-full bg-primary text-white shadow-float flex items-stretch overflow-hidden"
            >
               <button
                  ref="cartToggleEl"
                  type="button"
                  data-testid="cart-toggle"
                  class="flex flex-1 min-w-0 items-center gap-4 pl-5 pr-4 text-left"
                  :aria-expanded="isCartOpen"
                  aria-controls="cart-preview"
                  @click="toggleCart"
               >
                  <span ref="cartBagEl" class="relative flex items-center">
                     <AppIcon name="bag" weight="light" class="text-[24px]" />
                     <span ref="cartBadgeEl" class="absolute -top-1 -right-2 min-w-[18px] h-[18px] px-1 rounded-full bg-white text-primary text-[11px] font-semibold flex items-center justify-center leading-none">
                        <RollingNumber :value="cartCount" />
                     </span>
                  </span>
                  <AnimatedNumber class="text-[17px] font-medium" :value="cartTotalCents" :format="formatTotal" :from-zero="false" />
                  <AppIcon
                     name="caret-down"
                     class="cart-chevron ml-auto text-[15px] text-white/70"
                     :class="{ 'is-open': isCartOpen }"
                  />
               </button>
               <span class="w-px my-3 bg-white/20" aria-hidden="true"></span>
               <button
                  type="button"
                  data-testid="checkout-bar"
                  class="px-5 text-[15px] font-medium whitespace-nowrap"
                  @click="openCheckout"
               >
                  {{ t.checkout }}
               </button>
            </div>
         </div>
      </div>
    </Transition>

    <!-- Tab bar: a short line marks the current tab and springs between slots -->
    <nav ref="navEl" class="student-nav absolute bottom-0 inset-x-0 z-30 bg-surface-light border-t border-line" :aria-label="language === 'cn' ? '主导航' : 'Main'">
      <div class="student-nav-items relative mx-auto max-w-lg grid grid-cols-4">
        <div
          class="absolute left-0 top-0 w-1/4 transition-transform duration-spring ease-spring pointer-events-none"
          :style="{ transform: `translateX(${tabIndex * 100}%)` }"
          aria-hidden="true"
        >
          <span class="block mx-auto h-[2px] w-5 rounded-full bg-text-main"></span>
        </div>
        <button
          v-for="tab in TABS"
          :key="tab.id"
          type="button"
          @click="currentTab = tab.id"
          :aria-current="currentTab === tab.id ? 'page' : undefined"
          class="relative flex flex-col items-center justify-center gap-1 transition-colors duration-color"
          :class="currentTab === tab.id ? 'text-text-main' : 'text-text-sub'"
        >
          <span class="relative">
            <!-- Frequent navigation stays quiet: a one-pixel lift and weight
                 change acknowledge the tap; the line carries the distance. -->
            <span class="nav-icon-shell inline-flex" :class="{ 'is-active': currentTab === tab.id }">
              <AppIcon
                :name="tab.icon"
                :weight="currentTab === tab.id ? 'fill' : 'light'"
                class="text-[24px]"
              />
            </span>
            <span v-if="tab.id === 'pickup' && activeOrderCount > 0" class="absolute -top-1 -right-2.5 min-w-4 h-4 px-1 rounded-full bg-primary text-white text-[10px] font-semibold leading-none flex items-center justify-center ring-2 ring-white pop-in">
              <RollingNumber :value="activeOrderCount" />
            </span>
          </span>
          <span class="text-[12px] tracking-wide" :class="currentTab === tab.id ? 'font-semibold' : 'font-medium'">{{ tabLabel(tab.id) }}</span>
        </button>
      </div>
    </nav>
    </div>

    <Transition name="sheet">
      <div v-if="isCheckoutOpen" class="absolute inset-0 z-[100]">
         <CheckoutView @navigate="isCheckoutOpen = false" :cart="cart" :balance="userProfile.balance" :placing="placing" :payment-pending="paymentPending" :done="orderDone" @place-order="handlePlaceOrder" @update-quantity="updateCartItemQuantity" @remove-item="removeCartItem" :lang="language" />
      </div>
    </Transition>

    <ProductModal
      v-if="selectedProduct"
      ref="productSheet"
      :key="selectedProduct.id"
      :product="selectedProduct"
      :lang="language"
      @close="handleCloseProduct"
      @add-to-cart="handleAddToCart"
    />
  </div>
</template>
