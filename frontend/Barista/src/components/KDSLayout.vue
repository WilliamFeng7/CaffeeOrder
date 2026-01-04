<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useToastStore } from '../stores/toast';
import { ref, onMounted, onUnmounted, computed } from 'vue';

const router = useRouter();
const toastStore = useToastStore();
const currentTime = ref('');
const currentDate = ref('');

const handleLogout = () => {
  sessionStorage.removeItem('coffee_access_token');
  router.push('/login');
};

const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  currentDate.value = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
};

let timeInterval: number | null = null;
onMounted(() => {
  updateTime();
  timeInterval = setInterval(updateTime, 1000) as unknown as number;
});

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval);
});

const noiseTexture = "data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E";
</script>

<template>
  <div class="fixed inset-0 w-full h-full bg-background-light overflow-hidden font-sans select-none flex flex-col z-0">
    <!-- Background Noise Texture -->
    <div class="fixed inset-0 pointer-events-none z-50 opacity-[0.03] mix-blend-overlay" :style="{ backgroundImage: `url('${noiseTexture}')` }"></div>

    <!-- Header -->
    <header class="py-3 md:py-4 px-4 md:px-6 flex flex-wrap items-center justify-between gap-3 z-10 bg-background-light/90 backdrop-blur-md border-b border-gray-100/50 sticky top-0">
      <!-- Left: Brand -->
      <div class="flex items-center gap-3">
        <div class="size-10 md:size-11 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/20">
          <span class="material-symbols-rounded text-secondary text-xl md:text-2xl">coffee_maker</span>
        </div>
        <div class="flex flex-col">
          <span class="text-xs md:text-sm font-black text-primary leading-tight">Kitchen Display</span>
          <div class="flex items-center gap-1.5">
            <span class="size-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span class="text-[9px] md:text-[10px] font-bold text-text-sub uppercase tracking-wide">Online</span>
          </div>
        </div>
      </div>

      <!-- Center: Time -->
      <div class="flex flex-col items-center order-last lg:order-none w-full lg:w-auto">
        <div class="text-2xl md:text-3xl font-black text-primary font-mono tracking-tight leading-none">
          {{ currentTime }}
        </div>
        <div class="text-[10px] font-bold text-text-sub uppercase tracking-wide">
          {{ currentDate }}
        </div>
      </div>

      <!-- Right: Actions -->
      <div class="flex items-center gap-2">
        <button 
          @click="handleLogout"
          class="flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-xl bg-white text-text-main font-bold text-xs md:text-sm shadow-sm border border-gray-100 active:scale-95 transition-all hover:shadow-md"
        >
          <span class="material-symbols-rounded text-lg opacity-60">logout</span>
          <span class="hidden sm:inline">Exit</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 w-full overflow-auto relative z-0 p-3 md:p-5">
      <slot></slot>
    </main>

    <!-- Global Toast -->
    <div class="fixed top-16 md:top-20 left-0 right-0 z-[120] flex flex-col items-center gap-2 pointer-events-none px-4">
      <div 
        v-for="toast in toastStore.toasts" 
        :key="toast.id" 
        class="bg-primary text-white px-4 py-2.5 rounded-xl shadow-xl flex items-center gap-2.5 animate-slide-down-content pointer-events-auto max-w-sm"
      >
        <span class="material-symbols-rounded text-lg filled" :class="{
          'text-secondary': toast.type === 'success',
          'text-red-400': toast.type === 'error',
          'text-blue-400': toast.type === 'info'
        }">
          {{ toast.type === 'success' ? 'check_circle' : toast.type === 'error' ? 'error' : 'info' }}
        </span>
        <span class="text-sm font-semibold">{{ toast.message }}</span>
      </div>
    </div>
  </div>
</template>
