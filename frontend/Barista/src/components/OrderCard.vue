<script setup lang="ts">
import type { Order } from '../api';
import { computed, ref, onMounted, onUnmounted } from 'vue';

const props = defineProps<{
  order: Order;
}>();

const emit = defineEmits<{
  (e: 'update-status', orderId: number, status: string): void;
}>();

// Time elapsed (updates every 30 seconds)
const timeElapsed = ref('');
const updateTimeElapsed = () => {
  const totalSec = Math.floor((Date.now() - new Date(props.order.created_at).getTime()) / 1000);
  const min = Math.floor(totalSec / 60);
  if (min < 60) {
    timeElapsed.value = `${min}m`;
  } else {
    const h = Math.floor(min / 60);
    const m = min % 60;
    timeElapsed.value = `${h}h${m > 0 ? ` ${m}m` : ''}`;
  }
};

let timeInterval: number | null = null;
onMounted(() => {
  updateTimeElapsed();
  timeInterval = setInterval(updateTimeElapsed, 30000) as unknown as number;
});
onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval);
});

const formatTime = (isoString: string) => {
  return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
};

const waitMinutes = computed(() => Math.floor((Date.now() - new Date(props.order.created_at).getTime()) / 60000));

const isUrgent = computed(() => {
  if (['completed', 'cancelled', 'done'].includes(props.order.status.toLowerCase())) return false;
  return waitMinutes.value > 10;
});

const nextAction = computed(() => {
  const s = props.order.status.toLowerCase();
  if (['pending', 'new'].includes(s)) return { label: 'Start', action: 'processing', icon: 'play_arrow', style: 'bg-primary text-white' };
  if (['processing', 'inprogress'].includes(s)) return { label: 'Done', action: 'completed', icon: 'check', style: 'bg-secondary text-secondary-content' };
  return null;
});

const itemCount = computed(() => props.order.items.reduce((sum, item) => sum + item.quantity, 0));
</script>

<template>
  <div 
    class="bg-gray-50 p-3 rounded-2xl relative overflow-hidden transition-all duration-300 ease-luxury group hover:bg-white hover:shadow-sm"
    :class="{ 'ring-2 ring-red-400/50 bg-red-50': isUrgent }"
  >
    <!-- Order Header -->
    <div class="flex items-center justify-between gap-2 mb-2">
      <div class="flex items-center gap-2">
        <!-- Order Number Badge -->
        <div class="size-10 rounded-xl bg-primary text-white flex items-center justify-center font-black text-sm shadow-sm">
          #{{ order.id }}
        </div>
        <div class="flex flex-col">
          <span class="text-xs font-bold text-text-main">{{ formatTime(order.created_at) }}</span>
          <span class="text-[10px] font-semibold" :class="isUrgent ? 'text-red-500' : 'text-text-sub'">
            {{ timeElapsed }}
          </span>
        </div>
      </div>
      
      <!-- Item Count & Urgent Badge -->
      <div class="flex items-center gap-1.5">
        <span class="text-[10px] font-bold text-text-sub bg-white px-2 py-0.5 rounded-md">{{ itemCount }} items</span>
        <div v-if="isUrgent" class="size-6 rounded-md bg-red-500 flex items-center justify-center">
          <span class="material-symbols-rounded text-white text-sm">priority_high</span>
        </div>
      </div>
    </div>

    <!-- Compact Items List -->
    <div class="space-y-1.5 mb-2.5">
      <div v-for="(item, i) in order.items" :key="i" class="flex items-center gap-2 py-1 px-2 bg-white rounded-lg">
        <!-- Quantity -->
        <span class="size-5 rounded bg-primary/10 text-primary text-[10px] font-black flex items-center justify-center shrink-0">
          {{ item.quantity }}×
        </span>
        
        <!-- Name -->
        <span class="text-xs font-bold text-text-main flex-1 truncate">{{ item.name }}</span>
        
        <!-- Options -->
        <div class="flex items-center gap-1 shrink-0">
          <span v-if="item.temperature" class="text-[9px] font-bold px-1 py-0.5 rounded" :class="item.temperature === 'Hot' ? 'bg-red-50 text-red-500' : 'bg-blue-50 text-blue-500'">
            {{ item.temperature === 'Hot' ? '🔥' : '❄️' }}
          </span>
          <span v-if="item.sugar" class="text-[9px] font-bold px-1 py-0.5 rounded bg-amber-50 text-amber-600">{{ item.sugar }}</span>
        </div>
      </div>
    </div>

    <!-- Action Button -->
    <button 
      v-if="nextAction"
      @click="emit('update-status', order.id, nextAction.action)"
      class="w-full py-2 rounded-xl text-xs font-black shadow active:scale-[0.97] transition-all duration-200 flex items-center justify-center gap-1.5"
      :class="nextAction.style"
    >
      <span class="material-symbols-rounded text-base">{{ nextAction.icon }}</span>
      <span>{{ nextAction.label }}</span>
    </button>
    
    <!-- Done State -->
    <div v-else class="w-full py-2 rounded-xl bg-emerald-100 text-emerald-600 text-xs font-bold text-center flex items-center justify-center gap-1.5">
      <span class="material-symbols-rounded text-base filled">check_circle</span>
      Ready
    </div>
  </div>
</template>
