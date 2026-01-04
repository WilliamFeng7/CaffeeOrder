<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useToastStore } from '../stores/toast';
import { ref, onMounted, onUnmounted } from 'vue';

const router = useRouter();
const toast = useToastStore();
const currentTime = ref('');

const handleLogout = () => {
  sessionStorage.removeItem('coffee_access_token');
  router.push('/login');
};

const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
};

let timeInterval: number | null = null;
onMounted(() => {
  updateTime();
  timeInterval = setInterval(updateTime, 1000) as unknown as number;
});

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval);
});
</script>

<template>
  <div class="fixed inset-0 w-full h-full bg-background-light overflow-hidden font-sans select-none flex flex-col z-0">
    <!-- Background Noise Texture (Matches Student App) -->
    <div class="fixed inset-0 pointer-events-none z-50 opacity-[0.04] mix-blend-overlay" style="background-image: url(&quot;data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E&quot;);"></div>

    <!-- Header (Matches Student App HomeView Header Style) -->
    <header class="pt-6 md:pt-8 pb-4 px-4 md:px-8 flex flex-wrap items-end justify-between gap-4 z-10 bg-background-light/80 backdrop-blur-md sticky top-0">
      <div class="flex flex-col gap-1">
        <!-- Brand Status Line -->
        <div class="flex items-center gap-3 mb-1 animate-slide-down-content">
          <span class="material-symbols-rounded text-primary text-2xl md:text-3xl">storefront</span>
          <span class="text-[10px] md:text-[12px] font-black text-text-sub uppercase tracking-[0.3em]">OTIA DOWNTOWN</span>
          <span class="bg-primary text-white text-[9px] md:text-[10px] font-black px-3 md:px-4 py-1.5 md:py-2 rounded-full flex items-center gap-2 shadow-lg shadow-primary/20">
            <span class="size-1.5 rounded-full bg-white animate-pulse"></span>
            KDS ACTIVE
          </span>
        </div>
        
        <!-- Big Title -->
        <h1 class="text-3xl md:text-5xl font-sans font-black text-primary leading-[0.95] tracking-tighter transform-gpu animate-text-reveal">
          Kitchen Display
        </h1>
      </div>

      <!-- Right: Actions -->
      <div class="flex items-center gap-3 md:gap-4">
        <!-- Clock Display (Student Style) -->
        <div class="bg-white px-4 py-2.5 rounded-full shadow-sm border border-gray-100 font-mono text-lg md:text-xl font-bold text-primary tracking-tight">
          {{ currentTime }}
        </div>
        
        <!-- Logout Button (Styled like Student Quick Nav) -->
        <button 
          @click="handleLogout"
          class="flex items-center gap-2 px-5 md:px-6 py-2.5 md:py-3 rounded-full bg-white text-text-main font-bold text-sm shadow-sm border border-gray-100 active:scale-95 transition-all duration-300 ease-luxury hover:shadow-md"
        >
          <span class="hidden md:inline">Logout</span>
          <span class="material-symbols-rounded text-xl opacity-50">logout</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 w-full h-full overflow-auto relative z-0 p-4 md:p-6 pt-2">
      <slot></slot>
    </main>

    <!-- Global Toast (Positioned Top Center like Student App) -->
    <div class="fixed top-6 md:top-8 left-0 right-0 z-[120] flex flex-col items-center gap-3 pointer-events-none px-4">
      <div v-for="t in toast.toasts" :key="t.id" 
           class="bg-primary/95 backdrop-blur-xl text-white pl-4 pr-6 py-3 md:py-4 rounded-full shadow-[0_20px_60px_-10px_rgba(0,0,0,0.4)] flex items-center gap-3 md:gap-4 animate-slide-down-content pointer-events-auto border border-white/10 ring-1 ring-black/5"
      >
        <span class="material-symbols-rounded text-xl filled text-secondary animate-scale-up" v-if="t.type === 'success'">check_circle</span>
        <span class="material-symbols-rounded text-xl filled text-red-400 animate-scale-up" v-else-if="t.type === 'error'">error</span>
        <span class="material-symbols-rounded text-xl filled text-blue-400 animate-scale-up" v-else>info</span>
        <span class="text-sm font-bold tracking-tight">{{ t.message }}</span>
      </div>
    </div>
  </div>
</template>
