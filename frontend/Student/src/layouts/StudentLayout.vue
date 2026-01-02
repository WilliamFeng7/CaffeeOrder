<script setup lang="ts">
/**
 * StudentLayout.vue
 * Wrapper for the Student Application logic.
 */
import { ref, computed, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import HomeView from '../../components/HomeView.vue';
import MenuView from '../../components/MenuView.vue';
import ProductModal from '../../components/ProductModal.vue';
import CheckoutView from '../../components/CheckoutView.vue';
import PickupView from '../../components/PickupView.vue';
import SettingsView from '../../components/SettingsView.vue';
import { api } from '../../api';
import { PRODUCTS, TRANSLATIONS } from '../../data';
import { type CartItem, type Product, type Order, type Language, type TabState, type Toast, type UserProfile } from '../../types';

const router = useRouter();

// --- State ---
const currentTab = ref<TabState>('home');
const isCheckoutOpen = ref(false);
const cart = ref<CartItem[]>([]);
const selectedProduct = ref<Product | null>(null);
const language = ref<Language>('en');
const orders = ref<Order[]>([]);
const toasts = ref<Toast[]>([]);
const userProfile = ref<UserProfile>({
  name: '',
  phone: '',
  email: '',
  uuid: ''
});

const t = computed(() => TRANSLATIONS[language.value]);

// --- Lifecycle ---
onMounted(() => {
  const storedHistory = sessionStorage.getItem('otia_cafe_history');
  if (storedHistory) orders.value = JSON.parse(storedHistory);

  const storedProfile = sessionStorage.getItem('otia_cafe_profile');
  if (storedProfile) userProfile.value = JSON.parse(storedProfile);

  // Check Auth
  const token = sessionStorage.getItem('token');
  if (!token) {
    router.push('/login');
    return;
  }
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
    if (status && !status.is_open) {
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
  sessionStorage.removeItem('token');
  currentTab.value = 'home';
  addToast('Signed out successfully');
  router.push('/login');
};

// --- Methods ---
const addToast = (message: string, type: 'success' | 'info' = 'info') => {
  const id = Date.now().toString();
  toasts.value.push({ id, message, type });
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id);
  }, 3000);
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
    let finalPrice = selectedProduct.value.price;
    // Size price logic removed

    const newItem: CartItem = {
      ...selectedProduct.value,
      cartId: Math.random().toString(36).substr(2, 9),
      quantity: 1,
      price: finalPrice,
      size: 'Regular', // Fixed
      temperature: options.temp as any,
      sugar: options.sugar,
    };
    cart.value = [...cart.value, newItem];
    addToast(language.value === 'cn' ? '已成功加入购物车' : 'Added to cart successfully');
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
const fetchOrders = async () => {
  try {
     const fetchedOrders = await api.getMyOrders();
     orders.value = fetchedOrders;
  } catch (e) {
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
  try {
    if (cart.value.length === 0) return; 
    await api.createOrder(cart.value);
    await fetchOrders();
    await loadProfile(); // Refresh balance
    cart.value = [];
    isCheckoutOpen.value = false;
    currentTab.value = 'pickup';
    addToast(language.value === 'cn' ? '下单成功!' : 'Order placed successfully!');
  } catch (e: any) {
    const errorMsg = e.response?.data?.detail || e.message || 'Order failed';
    const displayMsg = language.value === 'cn' && errorMsg === 'Insufficient funds' ? '余额不足 (Insufficient Funds)' : errorMsg;
    addToast(displayMsg, 'info');
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
  } catch (e) {
    addToast(language.value === 'cn' ? "更新失败" : "Update failed", "info");
  }
};

const cartTotal = computed(() => cart.value.reduce((sum, item) => sum + (item.price * item.quantity), 0));
const cartCount = computed(() => cart.value.reduce((sum, item) => sum + item.quantity, 0));
const cartBump = ref(false);
watch(cartCount, (newCount) => {
  if (newCount > 0) {
    cartBump.value = true;
    setTimeout(() => cartBump.value = false, 300);
  }
});
</script>

<template>
  <div class="fixed inset-0 w-full h-full bg-background-light overflow-hidden font-sans select-none flex flex-col z-0">
    <div class="fixed top-8 left-0 right-0 z-[120] flex flex-col items-center gap-3 pointer-events-none">
      <div v-for="toast in toasts" :key="toast.id" class="bg-primary/95 backdrop-blur-xl text-white pl-4 pr-6 py-4 rounded-full shadow-[0_20px_60px_-10px_rgba(0,0,0,0.4)] flex items-center gap-4 animate-slide-down-content pointer-events-auto border border-white/10 ring-1 ring-black/5">
        <span class="material-symbols-rounded text-xl filled text-secondary animate-scale-up">check_circle</span>
        <span class="text-sm font-bold tracking-tight">{{ toast.message }}</span>
      </div>
    </div>

    <div class="flex-1 overflow-hidden relative w-full h-full z-0 transform-gpu pb-[104px]">
      <HomeView v-if="currentTab === 'home'" @navigate="(tab) => currentTab = tab" @quick-add="handleQuickAdd" :lang="language" :user-name="userProfile.name" />
      <MenuView v-if="currentTab === 'order'" :cart="cart" @select-product="handleSelectProduct" @remove-product-instance="handleRemoveProductInstance" :lang="language" @toggle-lang="handleToggleLang" @go-checkout="isCheckoutOpen = true" />
      <PickupView v-if="currentTab === 'pickup'" :orders="orders" :lang="language" />
      <SettingsView v-if="currentTab === 'profile'" :lang="language" @toggle-lang="handleToggleLang" :user-profile="userProfile" :orders="orders" @update-profile="handleUpdateProfile" @sign-out="handleSignOut" />
    </div>

    <div v-if="cartCount > 0 && !isCheckoutOpen && !selectedProduct && currentTab === 'order'" class="absolute bottom-[112px] md:bottom-[120px] left-0 right-0 z-50 pointer-events-none flex justify-center animate-slide-up-content transform-gpu">
       <div @click="isCheckoutOpen = true" data-testid="checkout-bar" class="pointer-events-auto bg-[#103E32] h-[72px] md:h-[84px] w-[90%] md:w-[600px] rounded-[42px] flex items-center justify-between p-2 pl-8 shadow-[0_30px_80px_-20px_rgba(16,62,50,0.6)] border border-[#ffffff10] transition-all duration-500 active:duration-300 ease-silk backdrop-blur-md relative overflow-hidden active:scale-[0.96]" :class="{ 'scale-[1.03]': cartBump }">
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12 translate-x-[-200%] animate-shimmer"></div>
          <div class="flex items-center gap-5 relative z-10">
             <div class="relative mt-0.5">
                <span class="material-symbols-rounded text-white text-[28px] md:text-[32px] font-light opacity-90 transition-transform duration-500 ease-silk">shopping_bag</span>
                <span class="absolute -top-1 -right-1.5 bg-[#EF4444] text-white text-[10px] font-bold size-4 md:size-5 rounded-full flex items-center justify-center border-[2px] border-[#103E32] shadow-sm animate-cart-bump">{{ cartCount }}</span>
             </div>
             <div class="flex flex-col justify-center">
                <span class="text-[20px] md:text-[24px] font-[800] text-white leading-none tracking-tight font-sans">¥{{ cartTotal.toFixed(2) }}</span>
                <span class="text-[9px] text-white/50 font-bold uppercase tracking-[0.2em] mt-0.5">Total</span>
             </div>
          </div>
          <button class="h-[60px] md:h-[68px] px-8 md:px-10 rounded-[34px] bg-white text-[#103E32] font-black text-base md:text-lg flex items-center gap-2 shadow-[0_4px_20px_rgba(0,0,0,0.1)] transition-all duration-500 ease-silk active:scale-[0.94] active:bg-[#f2f2f2] relative z-10">
            {{ t.checkout }}
            <span class="material-symbols-rounded text-xl md:text-2xl font-bold mt-0.5 transition-transform duration-500 ease-silk">arrow_forward</span>
          </button>
       </div>
    </div>

    <div class="absolute bottom-0 left-0 w-full z-30 pointer-events-auto bg-white border-t border-gray-100 shadow-[0_-5px_40px_rgba(0,0,0,0.02)] h-[96px] md:h-[104px] pb-[env(safe-area-inset-bottom,20px)] flex items-center justify-center md:rounded-b-[32px] transform-gpu">
      <div class="flex items-center justify-between px-6 w-full max-w-lg h-full">
        <button v-for="tab in (['home', 'order', 'pickup', 'profile'] as TabState[])" :key="tab" @click="currentTab = tab" class="relative flex items-center justify-center gap-2 rounded-full transition-[flex-grow,background-color,padding,width,transform] duration-700 active:duration-300 ease-silk outline-none transform-gpu will-change-[flex-grow, transform] active:scale-[0.88]" :class="currentTab === tab ? 'bg-primary text-white pl-6 pr-6 py-3.5 grow-[1.5] shadow-lg shadow-primary/20' : 'bg-transparent text-gray-300 w-16 py-3 grow-0 active:bg-gray-50'">
            <span class="material-symbols-rounded text-[28px] md:text-[30px] shrink-0 transition-all duration-700 active:duration-300 ease-silk" :class="{ 'filled': currentTab === tab }">
              {{ tab === 'home' ? 'storefront' : tab === 'order' ? 'local_cafe' : tab === 'pickup' ? 'shopping_bag' : 'person' }}
            </span>
            <span class="text-xs font-[800] uppercase tracking-widest whitespace-nowrap overflow-hidden transition-[max-width,opacity,transform] duration-700 active:duration-300 ease-silk" :class="currentTab === tab ? 'max-w-[100px] opacity-100 ml-1 translate-x-0' : 'max-w-0 opacity-0 ml-0 -translate-x-2'">
              {{ t[`nav${tab.charAt(0).toUpperCase() + tab.slice(1)}` as keyof typeof t] }}
            </span>
        </button>
      </div>
    </div>

    <div v-if="isCheckoutOpen" class="absolute inset-0 z-[100] bg-white animate-slide-up-modal">
       <CheckoutView @navigate="isCheckoutOpen = false" :cart="cart" @place-order="handlePlaceOrder" @update-quantity="updateCartItemQuantity" :lang="language" />
    </div>

    <ProductModal v-if="selectedProduct" :product="selectedProduct" @close="handleCloseProductModal" @add-to-cart="handleAddToCart" :lang="language" />
  </div>
</template>
