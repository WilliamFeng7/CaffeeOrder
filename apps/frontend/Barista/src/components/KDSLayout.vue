<script setup lang="ts">
/**
 * KDSLayout.vue
 * 
 * Premium Kitchen Display System layout - matching Student app aesthetic.
 * Features: Glass-morphism header, elegant brand, live clock, toast system.
 */
import { useRouter } from 'vue-router';
import { ref, onMounted, onUnmounted } from 'vue';
import { auth } from '@shared/auth';

const router = useRouter();
const currentTime = ref('');
const currentDate = ref('');

const handleLogout = () => {
  // Shared helper so the recorded role is cleared with the token (a hardcoded
  // key here left the role behind and could re-authorize the next session).
  auth.clearToken();
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
    
    <!-- Header: one compact row, so the order columns get the screen height -->
    <header class="py-2.5 md:py-3 px-4 md:px-6 flex items-center justify-between gap-4 z-10 bg-white/80 backdrop-blur-xl border-b border-gray-100/80 sticky top-0 shadow-[0_4px_30px_rgba(0,0,0,0.03)]">
      
      <!-- Left: Brand -->
      <div class="flex items-center gap-3">
        <div class="size-10 md:size-11 bg-gradient-to-br from-primary to-[#0A2921] rounded-[14px] md:rounded-[16px] flex items-center justify-center shadow-lg shadow-primary/25">
          <span class="material-symbols-rounded text-secondary text-2xl" aria-hidden="true">coffee_maker</span>
        </div>
        <div class="flex flex-col">
          <span class="text-base md:text-lg font-black text-primary leading-tight tracking-tight">Kitchen Display</span>
          <div class="flex items-center gap-2">
            <span class="size-2 rounded-full bg-emerald-500 animate-pulse shadow-sm shadow-emerald-500/50" aria-hidden="true"></span>
            <span class="text-[10px] md:text-xs font-bold text-text-sub uppercase tracking-widest">Live</span>
          </div>
        </div>
      </div>

      <!-- Center: Time -->
      <div class="hidden md:flex items-baseline gap-3 bg-white/80 px-5 py-1.5 rounded-2xl border border-gray-100/50 shadow-sm">
        <div class="text-2xl lg:text-3xl font-black text-primary font-mono tracking-tight leading-none tabular-nums">
          {{ currentTime }}
        </div>
        <div class="text-[11px] font-bold text-text-sub uppercase tracking-widest">
          {{ currentDate }}
        </div>
      </div>

      <!-- Right: Actions -->
      <div class="flex items-center gap-3">
        <!-- Mobile Time -->
        <div class="md:hidden flex flex-col items-end">
          <span class="text-lg font-black text-primary font-mono tabular-nums">{{ currentTime }}</span>
        </div>
        
        <button 
          type="button"
          @click="handleLogout"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl md:rounded-2xl bg-white text-text-main font-bold text-xs md:text-sm shadow-sm border border-gray-100 hover:shadow-md hover:border-gray-200"
        >
          <span class="material-symbols-rounded text-lg md:text-xl opacity-60" aria-hidden="true">logout</span>
          <span class="hidden sm:inline">Sign Out</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 w-full overflow-hidden relative z-0 p-3 md:p-4 lg:p-5">
      <slot></slot>
    </main>
    <!-- Toasts are rendered globally in App.vue (single renderer) -->
  </div>
</template>
