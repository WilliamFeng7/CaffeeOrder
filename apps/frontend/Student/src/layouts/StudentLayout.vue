<script setup lang="ts">
/**
 * StudentLayout.vue
 * Wrapper for the Student Application logic.
 */
import AppIcon from '@/components/AppIcon.vue';
import AnimatedNumber from '@shared/components/AnimatedNumber.vue';
import RollingNumber from '@shared/components/RollingNumber.vue';
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import MenuView from '../views/MenuView.vue';
import ProductModal from '../components/ProductModal.vue';
import CheckoutView from '../views/CheckoutView.vue';
import PickupView from '../views/PickupView.vue';
import SettingsView from '../views/SettingsView.vue';
import { api } from '../api';
import { PRODUCTS, TRANSLATIONS } from '../data';
import { formatCents, sumCents } from '../utils/money';
import { useToastStore } from '../stores/toast';
import { type CartItem, type Product, type Order, type Language, type TabState, type UserProfile, type SheetCloseReason } from '../types';
import { auth } from '@shared/auth';
import type { IconName } from '@/icons';
import { canMorph, morph, onScreen } from '../composables/morph';
import { motionMs } from '@shared/motion';
import { openSheets } from '../composables/stage';

const router = useRouter();

// --- State ---
const currentTab = ref<TabState>('home');
const isCheckoutOpen = ref(false);
const cart = ref<CartItem[]>([]);
const selectedProduct = ref<Product | null>(null);
const language = ref<Language>('en');
const orders = ref<Order[]>([]);
const shopOpen = ref(true);
const placing = ref(false);
const toastStore = useToastStore();
const userProfile = ref<UserProfile>({
  name: '',
  phone: '',
  email: '',
  uuid: ''
});

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
});

// --- Lifecycle ---
const readStoredJSON = <T,>(key: string): T | null => {
  // A corrupted/truncated sessionStorage entry used to throw out of onMounted
  // and leave the whole app blank; tolerate it and fall back to a fresh load.
  const raw = sessionStorage.getItem(key);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    sessionStorage.removeItem(key);
    return null;
  }
};

onMounted(() => {
  // Auth first: reading another account's cached history before we know who is
  // logged in is what let stale data flash on screen after an account switch.
  if (!auth.isLoggedIn()) {
    router.push('/login');
    return;
  }

  const storedHistory = readStoredJSON<Order[]>('otia_cafe_history');
  if (storedHistory) orders.value = storedHistory;

  const storedProfile = readStoredJSON<UserProfile>('otia_cafe_profile');
  if (storedProfile) userProfile.value = storedProfile;

  loadMenuData();
  loadProfile();
  checkShopStatus();
});

const loadProfile = async () => {
  try {
    const profile = await api.getProfile();
    userProfile.value = {
      name: profile.name,
      phone: profile.phone,
      email: profile.email,
      uuid: profile.uuid,
      balance: profile.balance,
      username: profile.username
    };
  } catch (e) {
    console.error("Failed to load profile", e);
  }
};

const checkShopStatus = async () => {
    const status = await api.getShopStatus();
    shopOpen.value = !(status && status.is_open === false);
    if (!shopOpen.value) {
        addToast(language.value === 'cn' ? '店铺已打烊' : 'Shop is currently closed', 'info');
    }
};

const loadMenuData = async () => {
  try {
    const items = await api.getMenu();
    if (items && items.length > 0) {
      PRODUCTS.splice(0, PRODUCTS.length, ...items);
    }
  } catch (e) {
    console.error("Failed to load menu", e);
  }
};

const handleSignOut = () => {
  auth.clearToken();

  // Signing out has to tear down everything that describes the *previous*
  // account. PRODUCTS is a module-level reactive singleton, and the order
  // history / profile were mirrored into sessionStorage, so clearing only the
  // token left the next user's first render populated with the old user's
  // cart, balances and order history (until a fetch happened to overwrite it).
  cart.value = [];
  orders.value = [];
  selectedProduct.value = null;
  userProfile.value = { name: '', phone: '', email: '', uuid: '' };
  PRODUCTS.splice(0, PRODUCTS.length);
  sessionStorage.removeItem('otia_cafe_history');
  sessionStorage.removeItem('otia_cafe_profile');

  currentTab.value = 'home';
  addToast('Signed out successfully');
  router.push('/login');
};

// --- Methods ---
// Toasts go through the shared store instead of a second, app-local queue.
const addToast = (message: string, type: 'success' | 'info' | 'error' | 'warning' = 'info') => {
  toastStore.addToast(message, type);
};

// --- Product sheet ---------------------------------------------------------
// The photo grows out of the tapped card, and on close flies back into it
// (or, after "Add", into the cart bar). See composables/morph.ts.
const productSheet = ref<InstanceType<typeof ProductModal> | null>(null);
const cartIconEl = ref<HTMLElement | null>(null);
const heroOpen = ref(false);
let productOrigin: HTMLElement | null = null;
let productClosing = false;

const handleSelectProduct = (product: Product, origin?: HTMLElement | null) => {
  if (selectedProduct.value) return;
  productOrigin = origin ?? null;
  productClosing = false;
  heroOpen.value = canMorph() && onScreen(origin);
  void morph('open', heroOpen.value ? origin : null, () => {
    selectedProduct.value = product;
  }, () => productSheet.value?.photo);
};

const handleCloseProduct = async (reason: SheetCloseReason) => {
  const sheet = productSheet.value;
  if (!sheet || productClosing) return;
  productClosing = true;
  const unmount = () => { selectedProduct.value = null; };

  // Dragged away: the sheet is already off-screen.
  if (reason === 'dragged') {
    unmount();
    return;
  }

  const photo = sheet.photo;
  const flies = canMorph() && onScreen(photo) && (reason === 'added' || onScreen(productOrigin));
  if (flies) {
    await morph(reason === 'added' ? 'cart' : 'close', photo, unmount,
      () => (reason === 'added' ? cartIconEl.value : productOrigin));
  } else {
    await sheet.leave();
    unmount();
  }
  // The bar swells a touch as the item lands in it.
  if (reason === 'added') bumpCart();
};

// 切换语言时整屏文字交叉淡入，而不是一帧之内全部换掉 (a crossfade with a
// hint of blur, so the two languages never read as a double exposure).
const handleToggleLang = () => {
  const swap = () => { language.value = language.value === 'en' ? 'cn' : 'en'; };
  const start = (document as Document & { startViewTransition?: (cb: () => Promise<void>) => unknown }).startViewTransition;
  if (typeof start !== 'function' || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    swap();
    return;
  }
  const root = document.documentElement;
  root.dataset.morph = 'lang';
  const vt = start.call(document, async () => { swap(); await nextTick(); }) as { finished: Promise<void> };
  void vt.finished.finally(() => { if (root.dataset.morph === 'lang') delete root.dataset.morph; });
};

// --- 背景后缩 (the app recedes behind the product sheet) -----------------------
// Like an iOS sheet: the page behind scales back a little and rounds its
// corners over a dark backstage, so the sheet reads as a layer on top.
const stageReceded = computed(() => !!selectedProduct.value || openSheets.value > 0);
const stageRounded = ref(false);
let roundTimer: number | undefined;
watch(stageReceded, (receded) => {
  window.clearTimeout(roundTimer);
  if (receded) stageRounded.value = true;
  else roundTimer = window.setTimeout(() => { stageRounded.value = false; }, motionMs('--dur-sheet-in', 560));
});

const handleAddToCart = (options: { size: string; temp: string; sugar: string }) => {
  if (selectedProduct.value) {
    const finalPrice = selectedProduct.value.price;

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
      size: 'Regular', // Fixed
      temperature: options.temp as any,
      sugar: options.sugar,
    };
    cart.value = [...cart.value, newItem];
    // The sheet shows "Added" and the photo flies into the cart bar, which
    // lives on the Order tab.
    currentTab.value = 'order';
  }
};

const handleRemoveProductInstance = (productId: string) => {
  const lastIndex = cart.value.map(item => item.id).lastIndexOf(productId);
  if (lastIndex !== -1) {
    const newCart = [...cart.value];
    newCart.splice(lastIndex, 1);
    cart.value = newCart;
  }
};

const updateCartItemQuantity = (cartId: string, delta: number) => {
  cart.value = cart.value.map(item => {
    if (item.cartId === cartId) return { ...item, quantity: Math.max(0, item.quantity + delta) };
    return item;
  }).filter(item => item.quantity > 0);
};

let pollInterval: any = null;
const startPolling = () => {
  if (pollInterval) clearInterval(pollInterval);
  fetchOrders();
  pollInterval = setInterval(fetchOrders, 3000);
};
const stopPolling = () => {
  if (pollInterval) clearInterval(pollInterval);
};

// Never leak the polling interval when the layout unmounts
// (e.g. router-guard redirect on expired token)
onUnmounted(stopPolling);
// Stage of each order at the previous poll, so an order that turns "ready"
// raises one notice instead of relying on the student watching the card.
let lastStages: Map<string, string> | null = null;
const fetchOrders = async () => {
  try {
     const fetchedOrders = await api.getMyOrders();
     if (lastStages) {
       for (const o of fetchedOrders) {
         const before = lastStages.get(o.id);
         if (o.stage === 'ready' && before && before !== 'ready') {
           addToast(`${t.value.orderReady} ${o.dailyNumber}`, 'success');
         }
       }
     }
     lastStages = new Map(fetchedOrders.map(o => [o.id, o.stage]));
     orders.value = fetchedOrders;
  } catch {
     console.error("Failed to fetch orders");
  }
};

watch(currentTab, (newTab) => {
  if (newTab === 'pickup' || newTab === 'profile') {
    startPolling();
  } else {
    stopPolling();
  }
});

// 下单成功的一瞬 (the order went through): the pay button draws a check
// and holds it for a beat before the sheet slides away to Pickup.
const orderDone = ref(false);
watch(isCheckoutOpen, (open) => { if (open) orderDone.value = false; });

const handlePlaceOrder = async () => {
  // A second tap while the first request is in flight used to place (and
  // charge) the same cart twice.
  if (placing.value || cart.value.length === 0) return;
  placing.value = true;
  try {
    await api.createOrder(cart.value);
    orderDone.value = true;
    const shownAt = performance.now();
    await fetchOrders();
    await loadProfile(); // Refresh balance
    const hold = motionMs('--dur-enter', 560) + 180 - (performance.now() - shownAt);
    if (hold > 0) await new Promise((resolve) => window.setTimeout(resolve, hold));
    cart.value = [];
    isCheckoutOpen.value = false;
    currentTab.value = 'pickup';
    addToast(language.value === 'cn' ? '下单成功!' : 'Order placed successfully!', 'success');
  } catch (e: any) {
    const errorMsg = e.response?.data?.detail || e.message || 'Order failed';
    const displayMsg = language.value === 'cn' && errorMsg === 'Insufficient funds' ? '余额不足 (Insufficient Funds)' : errorMsg;
    addToast(displayMsg, 'info');
  } finally {
    placing.value = false;
  }
};

const handleUpdateProfile = async (p: UserProfile) => {
  try {
    const updated = await api.updateProfile(p);
    userProfile.value = updated;
    addToast(language.value === 'cn' ? "个人信息已更新" : "Profile updated", "success");
  } catch {
    addToast(language.value === 'cn' ? "更新失败" : "Update failed", "info");
  }
};

// Integer cents, so a multi-item cart cannot drift a cent away from the total
// the server computes (see utils/money.ts).
const cartTotalCents = computed(() => sumCents(cart.value));
const cartCount = computed(() => cart.value.reduce((sum, item) => sum + item.quantity, 0));
const formatTotal = (cents: number) => `¥${formatCents(Math.round(cents))}`;
const cartBump = ref(false);
const bumpCart = () => {
  // Swell briefly, then spring back (the bar's ease-spring transition).
  cartBump.value = true;
  window.setTimeout(() => { cartBump.value = false; }, 180);
};
</script>

<template>
  <div class="fixed inset-0 w-full h-full bg-background-light overflow-hidden font-sans text-text-main select-none z-0">
    <!-- Toasts are rendered once, globally, by <ToastContainer /> in App.vue. -->

    <!-- Dark backstage, only seen around the receded app while a sheet is up -->
    <div v-if="stageRounded" class="absolute inset-0 bg-[#141816]" aria-hidden="true"></div>

    <!-- The app itself: recedes behind the product sheet -->
    <div class="app-stage absolute inset-0 flex flex-col bg-background-light" :class="{ 'is-receded': stageReceded, 'is-rounded': stageRounded }">
    <div class="flex-1 overflow-hidden relative w-full h-full z-0 pb-[calc(64px+env(safe-area-inset-bottom))] md:pb-[calc(72px+env(safe-area-inset-bottom))]">
      <!-- KeepAlive: switching tabs keeps each tab's scroll position, category
           and sub-view; the Transition slides the new tab in from its side.
           The leaving tab is positioned against the inner box (not the padded
           one), so its scroll area keeps its size while it fades out. -->
      <div class="relative h-full">
        <Transition :name="`tab-${tabDir}`">
          <KeepAlive>
            <HomeView v-if="currentTab === 'home'" @navigate="(tab) => currentTab = tab" @quick-add="handleSelectProduct" :lang="language" :user-name="userProfile.name" :shop-open="shopOpen" />
            <MenuView v-else-if="currentTab === 'order'" :cart="cart" @select-product="handleSelectProduct" @remove-product-instance="handleRemoveProductInstance" :lang="language" @toggle-lang="handleToggleLang" @go-checkout="isCheckoutOpen = true" />
            <PickupView v-else-if="currentTab === 'pickup'" :orders="orders" :lang="language" :refresh="fetchOrders" />
            <SettingsView v-else-if="currentTab === 'profile'" :lang="language" @toggle-lang="handleToggleLang" :user-profile="userProfile" :orders="orders" @update-profile="handleUpdateProfile" @sign-out="handleSignOut" />
          </KeepAlive>
        </Transition>
      </div>
    </div>

    <!-- Cart bar: floats above the tab bar on the menu -->
    <Transition name="cartbar">
      <div v-if="cartCount > 0 && !isCheckoutOpen && !selectedProduct && currentTab === 'order'" class="absolute inset-x-0 bottom-[calc(76px+env(safe-area-inset-bottom))] md:bottom-[calc(88px+env(safe-area-inset-bottom))] z-40 flex justify-center px-4 pointer-events-none">
         <button
           type="button"
           @click="isCheckoutOpen = true"
           data-testid="checkout-bar"
           class="group pointer-events-auto w-full max-w-md h-14 rounded-full bg-primary text-white shadow-float flex items-center gap-4 pl-5 pr-6 transition-transform duration-spring ease-spring active:duration-press active:scale-[0.98]"
           :class="{ 'scale-[1.03]': cartBump }"
         >
            <span ref="cartIconEl" class="relative flex items-center">
               <AppIcon name="bag" weight="light" draw class="text-[24px]" />
               <span class="absolute -top-1 -right-2 min-w-[18px] h-[18px] px-1 rounded-full bg-white text-primary text-[11px] font-semibold flex items-center justify-center leading-none">
                  <RollingNumber :value="cartCount" />
               </span>
            </span>
            <AnimatedNumber class="text-[17px] font-medium" :value="cartTotalCents" :format="formatTotal" :from-zero="false" />
            <span class="ml-auto flex items-center gap-1.5 text-[15px] font-medium">
              {{ t.checkout }}
              <AppIcon name="arrow-right" class="text-base nudge" />
            </span>
         </button>
      </div>
    </Transition>

    <!-- Tab bar: a short line marks the current tab and springs between slots -->
    <nav class="absolute bottom-0 inset-x-0 z-30 bg-surface-light border-t border-line pb-[env(safe-area-inset-bottom)]" :aria-label="language === 'cn' ? '主导航' : 'Main'">
      <div class="relative mx-auto max-w-lg grid grid-cols-4 h-16 md:h-[72px]">
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
            <!-- Re-keyed on selection: the line is drawn again while the icon
                 dips and pops back (~8% overshoot) -->
            <AppIcon
              :key="currentTab === tab.id ? 'on' : 'off'"
              :name="tab.icon"
              :weight="currentTab === tab.id ? 'fill' : 'light'"
              :draw="currentTab === tab.id"
              class="text-[24px]"
              :class="{ 'animate-icon-pop': currentTab === tab.id }"
            />
            <span v-if="tab.id === 'pickup' && activeOrderCount > 0" class="absolute -top-1 -right-2.5 min-w-4 h-4 px-1 rounded-full bg-primary text-white text-[10px] font-semibold leading-none flex items-center justify-center ring-2 ring-white pop-in">
              <RollingNumber :value="activeOrderCount" />
            </span>
          </span>
          <span class="text-[11px] md:text-[12px] tracking-wide" :class="currentTab === tab.id ? 'font-semibold' : 'font-medium'">{{ tabLabel(tab.id) }}</span>
        </button>
      </div>
    </nav>
    </div>

    <Transition name="sheet">
      <div v-if="isCheckoutOpen" class="absolute inset-0 z-[100]">
         <CheckoutView @navigate="isCheckoutOpen = false" :cart="cart" :placing="placing" :done="orderDone" @place-order="handlePlaceOrder" @update-quantity="updateCartItemQuantity" :lang="language" />
      </div>
    </Transition>

    <ProductModal
      v-if="selectedProduct"
      ref="productSheet"
      :key="selectedProduct.id"
      :product="selectedProduct"
      :hero="heroOpen"
      :lang="language"
      @close="handleCloseProduct"
      @add-to-cart="handleAddToCart"
    />
  </div>
</template>
