<script setup lang="ts">
/**
 * KDSLayout.vue
 * 
 * Premium Kitchen Display System layout - matching Student app aesthetic.
 * Features: Glass-morphism header, elegant brand, live clock, toast system.
 */
import { useRouter } from 'vue-router';
import { ref, onMounted, onUnmounted } from 'vue';

const router = useRouter();
const currentTime = ref('');
const currentDate = ref('');

const handleLogout = () => {
  sessionStorage.removeItem('coffee_access_token');
  router.push('/login');
};

const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  currentDate.value = now.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' });
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
    
    <!-- Header -->
    <header class="py-4 md:py-5 px-5 md:px-8 flex items-center justify-between gap-4 z-10 bg-white/70 backdrop-blur-xl border-b border-gray-100/80 sticky top-0 shadow-[0_4px_30px_rgba(0,0,0,0.03)]">
      
      <!-- Left: Brand -->
      <div class="flex items-center gap-4">
        <div class="size-12 md:size-14 bg-gradient-to-br from-primary to-[#0A2921] rounded-[18px] md:rounded-[20px] flex items-center justify-center shadow-lg shadow-primary/25 transition-transform duration-500 ease-luxury active:scale-95">
          <span class="material-symbols-rounded text-secondary text-2xl md:text-3xl">coffee_maker</span>
        </div>
        <div class="flex flex-col">
          <span class="text-base md:text-lg font-black text-primary leading-tight tracking-tight">Kitchen Display</span>
          <div class="flex items-center gap-2">
            <span class="size-2 rounded-full bg-emerald-500 animate-pulse shadow-sm shadow-emerald-500/50"></span>
            <span class="text-[10px] md:text-xs font-bold text-text-sub uppercase tracking-widest">Live</span>
          </div>
        </div>
      </div>

      <!-- Center: Time -->
      <div class="hidden md:flex flex-col items-center bg-white/80 px-8 py-3 rounded-2xl border border-gray-100/50 shadow-sm">
        <div class="text-3xl lg:text-4xl font-black text-primary font-mono tracking-tight leading-none">
          {{ currentTime }}
        </div>
        <div class="text-[10px] font-bold text-text-sub uppercase tracking-widest mt-1">
          {{ currentDate }}
        </div>
      </div>

      <!-- Right: Actions -->
      <div class="flex items-center gap-3">
        <!-- Mobile Time -->
        <div class="md:hidden flex flex-col items-end">
          <span class="text-lg font-black text-primary font-mono">{{ currentTime }}</span>
        </div>
        
        <button 
          @click="handleLogout"
          class="flex items-center gap-2 px-4 md:px-5 py-2.5 md:py-3 rounded-xl md:rounded-2xl bg-white text-text-main font-bold text-xs md:text-sm shadow-sm border border-gray-100 active:scale-95 transition-all duration-300 hover:shadow-md hover:border-gray-200"
        >
          <span class="material-symbols-rounded text-lg md:text-xl opacity-50">logout</span>
          <span class="hidden sm:inline">Sign Out</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 w-full overflow-hidden relative z-0 p-4 md:p-6 lg:p-8">
      <slot></slot>
    </main>
    <!-- Toasts are rendered globally in App.vue (single renderer) -->
  </div>
</template>
