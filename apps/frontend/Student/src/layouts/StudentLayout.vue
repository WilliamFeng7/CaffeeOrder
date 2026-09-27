<script setup lang="ts">
/**
 * StudentLayout.vue
 * Wrapper for the Student Application logic.
 */
import AppIcon from '@shared/components/AppIcon.vue';
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
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
import { type CartItem, type Product, type Order, type Language, type TabState, type UserProfile } from '../types';
import { auth } from '@shared/auth';
import type { IconName } from '@shared/icons';

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
  { id: 'pickup', icon: 'receipt' },
  { id: 'profile', icon: 'user' },
];
const tabIndex = computed(() => Math.max(0, TABS.findIndex(tab => tab.id === currentTab.value)));
const tabLabel = (id: TabState) =>
  t.value[`nav${id.charAt(0).toUpperCase() + id.slice(1)}` as keyof typeof t.value] as string;
// 进行中的订单数，显示在「取餐」标签上
const activeOrderCount = computed(() => orders.value.filter(o => o.status === 'active').length);

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
// Student previously ran two toast systems at once (this hand-rolled one plus
// ToastContainer.vue), so a message could be raised in one and never rendered by
// the other. `addToast` keeps its old signature so the call sites above are
// unchanged.
const addToast = (message: string, type: 'success' | 'info' | 'error' | 'warning' = 'info') => {
  toastStore.addToast(message, type);
};

const handleSelectProduct = (product: Product) => {
  selectedProduct.value = null;
  setTimeout(() => {
    selectedProduct.value = product;
  }, 50);
};

const handleCloseProductModal = () => {
  selectedProduct.value = null;
};

const handleToggleLang = () => {
  language.value = language.value === 'en' ? 'cn' : 'en';
};

const handleAddToCart = (options: { size: string; temp: string; sugar: string }) => {
  if (selectedProduct.value) {
    const finalPrice = selectedProduct.value.price;
    // Size price logic removed

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
    addToast(language.value === 'cn' ? '已成功加入购物车' : 'Added to cart successfully', 'success');
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

const handlePlaceOrder = async () => {
  // A second tap while the first request is in flight used to place (and
  // charge) the same cart twice.
  if (placing.value || cart.value.length === 0) return;
  placing.value = true;
  try {
    await api.createOrder(cart.value);
    await fetchOrders();
    await loadProfile(); // Refresh balance
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

const handleQuickAdd = (product: Product) => {
    handleSelectProduct(product);
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
const cartBump = ref(false);
watch(cartCount, (newCount, oldCount) => {
  if (newCount > oldCount) {
    // Swell briefly, then spring back (see the bar's ease-spring transition).
    cartBump.value = true;
    setTimeout(() => cartBump.value = false, 180);
  }
});
</script>

<template>
  <div class="fixed inset-0 w-full h-full bg-background-light overflow-hidden font-sans text-text-main select-none flex flex-col z-0">
    <!-- Toasts are rendered once, globally, by the shared <ToastContainer /> mounted
         in App.vue. This layout used to run its own inline pill list on top of that,
         so a single message appeared twice. -->

    <div class="flex-1 overflow-hidden relative w-full h-full z-0 pb-[calc(64px+env(safe-area-inset-bottom))] md:pb-[calc(72px+env(safe-area-inset-bottom))]">
      <!-- KeepAlive: switching tabs keeps each tab's scroll position, category
           and sub-view instead of rebuilding it from the top every time. -->
      <KeepAlive>
        <HomeView v-if="currentTab === 'home'" @navigate="(tab) => currentTab = tab" @quick-add="handleQuickAdd" :lang="language" :user-name="userProfile.name" :shop-open="shopOpen" />
        <MenuView v-else-if="currentTab === 'order'" :cart="cart" @select-product="handleSelectProduct" @remove-product-instance="handleRemoveProductInstance" :lang="language" @toggle-lang="handleToggleLang" @go-checkout="isCheckoutOpen = true" />
        <PickupView v-else-if="currentTab === 'pickup'" :orders="orders" :lang="language" />
        <SettingsView v-else-if="currentTab === 'profile'" :lang="language" @toggle-lang="handleToggleLang" :user-profile="userProfile" :orders="orders" @update-profile="handleUpdateProfile" @sign-out="handleSignOut" />
      </KeepAlive>
    </div>

    <!-- Cart bar: floats above the tab bar on the menu -->
    <Transition name="cartbar">
      <div v-if="cartCount > 0 && !isCheckoutOpen && !selectedProduct && currentTab === 'order'" class="absolute inset-x-0 bottom-[calc(76px+env(safe-area-inset-bottom))] md:bottom-[calc(88px+env(safe-area-inset-bottom))] z-40 flex justify-center px-4 pointer-events-none">
         <button
           type="button"
           @click="isCheckoutOpen = true"
           data-testid="checkout-bar"
           class="pointer-events-auto w-full max-w-md h-14 rounded-full bg-primary text-white shadow-float flex items-center gap-3 pl-5 pr-6 transition-transform duration-spring ease-spring active:duration-press active:scale-[0.98]"
           :class="{ 'scale-[1.03]': cartBump }"
         >
            <span class="relative flex items-center">
               <AppIcon name="bag" class="text-[22px]" />
               <span :key="cartCount" class="absolute -top-1.5 -right-2.5 min-w-[18px] h-[18px] px-1 rounded-full bg-white text-primary text-[11px] font-semibold flex items-center justify-center tabular-nums animate-cart-bump">{{ cartCount }}</span>
            </span>
            <span class="ml-2 text-[17px] font-semibold tabular-nums">¥{{ formatCents(cartTotalCents) }}</span>
            <span class="ml-auto flex items-center gap-1.5 text-[15px] font-medium">
              {{ t.checkout }}
              <AppIcon name="arrow-right" class="text-base" />
            </span>
         </button>
      </div>
    </Transition>

    <!-- Tab bar: a thin line marks the current tab and springs between slots -->
    <nav class="absolute bottom-0 inset-x-0 z-30 bg-surface-light border-t border-line pb-[env(safe-area-inset-bottom)]" :aria-label="language === 'cn' ? '主导航' : 'Main'">
      <div class="relative mx-auto max-w-lg grid grid-cols-4 h-16 md:h-[72px]">
        <div
          class="absolute left-0 top-0 w-1/4 transition-transform duration-spring ease-spring pointer-events-none"
          :style="{ transform: `translateX(${tabIndex * 100}%)` }"
          aria-hidden="true"
        >
          <span class="block mx-auto h-[2px] w-6 rounded-full bg-primary"></span>
        </div>
        <button
          v-for="tab in TABS"
          :key="tab.id"
          type="button"
          @click="currentTab = tab.id"
          :aria-current="currentTab === tab.id ? 'page' : undefined"
          class="relative flex flex-col items-center justify-center gap-1"
          :class="currentTab === tab.id ? 'text-text-main' : 'text-text-sub'"
        >
          <span class="relative">
            <AppIcon
              :name="tab.icon"
              :weight="currentTab === tab.id ? 'fill' : 'regular'"
              class="text-[22px] transition-colors duration-color"
              :class="currentTab === tab.id ? 'text-primary' : ''"
            />
            <span v-if="tab.id === 'pickup' && activeOrderCount > 0" class="absolute -top-1 -right-2 min-w-4 h-4 px-1 rounded-full bg-primary text-white text-[10px] font-semibold leading-4 text-center tabular-nums ring-2 ring-white">{{ activeOrderCount }}</span>
          </span>
          <span class="text-[11px] tracking-wide transition-colors duration-color" :class="currentTab === tab.id ? 'font-semibold' : 'font-medium'">{{ tabLabel(tab.id) }}</span>
        </button>
      </div>
    </nav>

    <Transition name="sheet">
      <div v-if="isCheckoutOpen" class="absolute inset-0 z-[100]">
         <CheckoutView @navigate="isCheckoutOpen = false" :cart="cart" :placing="placing" @place-order="handlePlaceOrder" @update-quantity="updateCartItemQuantity" :lang="language" />
      </div>
    </Transition>

    <ProductModal v-if="selectedProduct" :product="selectedProduct" @close="handleCloseProductModal" @add-to-cart="handleAddToCart" :lang="language" />
  </div>
</template>
