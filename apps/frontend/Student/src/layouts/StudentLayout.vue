<script setup lang="ts">
/**
 * StudentLayout.vue
 * Wrapper for the Student Application logic.
 */
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
    cartBump.value = true;
    setTimeout(() => cartBump.value = false, 200);
  }
});
</script>

<template>
  <div class="fixed inset-0 w-full h-full bg-background-light overflow-hidden font-sans select-none flex flex-col z-0">
    <!-- Toasts are rendered once, globally, by the shared <ToastContainer /> mounted
         in App.vue. This layout used to run its own inline pill list on top of that,
         so a single message appeared twice. -->

    <div class="flex-1 overflow-hidden relative w-full h-full z-0 transform-gpu pb-[80px]">
      <HomeView v-if="currentTab === 'home'" @navigate="(tab) => currentTab = tab" @quick-add="handleQuickAdd" :lang="language" :user-name="userProfile.name" :shop-open="shopOpen" />
      <MenuView v-if="currentTab === 'order'" :cart="cart" @select-product="handleSelectProduct" @remove-product-instance="handleRemoveProductInstance" :lang="language" @toggle-lang="handleToggleLang" @go-checkout="isCheckoutOpen = true" />
      <PickupView v-if="currentTab === 'pickup'" :orders="orders" :lang="language" />
      <SettingsView v-if="currentTab === 'profile'" :lang="language" @toggle-lang="handleToggleLang" :user-profile="userProfile" :orders="orders" @update-profile="handleUpdateProfile" @sign-out="handleSignOut" />
    </div>

    <div v-if="cartCount > 0 && !isCheckoutOpen && !selectedProduct && currentTab === 'order'" class="absolute bottom-[84px] md:bottom-[100px] left-0 right-0 z-50 pointer-events-none flex justify-center animate-slide-up-content">
       <div @click="isCheckoutOpen = true" data-testid="checkout-bar" class="pointer-events-auto bg-[#103E32] h-[56px] md:h-[64px] w-[calc(100%-32px)] max-w-[560px] rounded-[32px] flex items-center justify-between p-1.5 pl-6 shadow-[0_24px_60px_-20px_rgba(16,62,50,0.6)] border border-[#ffffff10] transition-transform duration-200 ease-out relative overflow-hidden active:scale-[0.97]" :class="{ 'scale-[1.02]': cartBump }">
          <div class="flex items-center gap-5 relative z-10">
             <div class="relative mt-0.5">
                <span class="material-symbols-rounded text-white text-[28px] md:text-[30px] font-light opacity-90" aria-hidden="true">shopping_bag</span>
                <span :key="cartCount" class="absolute -top-1 -right-1.5 bg-[#EF4444] text-white text-[10px] font-bold size-4 md:size-5 rounded-full flex items-center justify-center border-[2px] border-[#103E32] shadow-sm animate-cart-bump">{{ cartCount }}</span>
             </div>
             <div class="flex flex-col justify-center">
                <span class="text-[20px] md:text-[24px] font-[800] text-white leading-none tracking-tight font-sans">¥{{ formatCents(cartTotalCents) }}</span>
                <span class="text-[9px] text-white/50 font-bold uppercase tracking-[0.2em] mt-0.5">Total</span>
             </div>
          </div>
          <button type="button" class="h-[44px] md:h-[52px] px-6 md:px-8 rounded-[26px] bg-white text-[#103E32] font-black text-sm md:text-base flex items-center gap-2 shadow-[0_4px_20px_rgba(0,0,0,0.1)] active:bg-[#f2f2f2] relative z-10">
            {{ t.checkout }}
            <span class="material-symbols-rounded text-xl md:text-2xl font-bold mt-0.5" aria-hidden="true">arrow_forward</span>
          </button>
       </div>
    </div>

    <div class="absolute bottom-0 left-0 w-full z-30 pointer-events-auto bg-white border-t border-gray-100 shadow-[0_-5px_40px_rgba(0,0,0,0.02)] h-[72px] md:h-[88px] pb-[env(safe-area-inset-bottom,12px)] flex items-center justify-center md:rounded-b-[32px] transform-gpu">
      <div class="flex items-center justify-between px-6 w-full max-w-lg h-full">
        <button v-for="tab in (['home', 'order', 'pickup', 'profile'] as TabState[])" :key="tab" type="button" @click="currentTab = tab" :aria-current="currentTab === tab ? 'page' : undefined" class="relative flex items-center justify-center gap-2 rounded-full transition-[flex-grow,background-color,padding,width,transform] duration-300 ease-silk outline-none" :class="currentTab === tab ? 'bg-primary text-white pl-6 pr-6 py-3.5 grow-[1.5] shadow-lg shadow-primary/20' : 'bg-transparent text-gray-400 w-16 py-3 grow-0 active:bg-gray-50'">
            <span class="material-symbols-rounded text-[28px] md:text-[30px] shrink-0" :class="{ 'filled': currentTab === tab }" aria-hidden="true">
              {{ tab === 'home' ? 'storefront' : tab === 'order' ? 'local_cafe' : tab === 'pickup' ? 'shopping_bag' : 'person' }}
            </span>
            <span class="text-xs font-[800] uppercase tracking-widest whitespace-nowrap overflow-hidden transition-[max-width,opacity,transform] duration-300 ease-silk" :class="currentTab === tab ? 'max-w-[100px] opacity-100 ml-1 translate-x-0' : 'max-w-0 opacity-0 ml-0 -translate-x-2'">
              {{ t[`nav${tab.charAt(0).toUpperCase() + tab.slice(1)}` as keyof typeof t] }}
            </span>
        </button>
      </div>
    </div>

    <Transition name="sheet">
      <div v-if="isCheckoutOpen" class="absolute inset-0 z-[100] bg-white">
         <CheckoutView @navigate="isCheckoutOpen = false" :cart="cart" :placing="placing" @place-order="handlePlaceOrder" @update-quantity="updateCartItemQuantity" :lang="language" />
      </div>
    </Transition>

    <ProductModal v-if="selectedProduct" :product="selectedProduct" @close="handleCloseProductModal" @add-to-cart="handleAddToCart" :lang="language" />
  </div>
</template>
