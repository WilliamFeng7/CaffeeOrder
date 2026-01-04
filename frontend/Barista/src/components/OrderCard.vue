<script setup lang="ts">
import type { Order } from '../api';
import { computed, ref, onMounted, onUnmounted } from 'vue';

const props = defineProps<{
  order: Order;
}>();

const emit = defineEmits<{
  (e: 'update-status', orderId: number, status: string): void;
}>();

// Time elapsed (updates every 30 seconds for better accuracy)
const timeElapsed = ref('');
const updateTimeElapsed = () => {
  const totalSec = Math.floor((Date.now() - new Date(props.order.created_at).getTime()) / 1000);
  const min = Math.floor(totalSec / 60);
  if (min < 60) {
    timeElapsed.value = `${min}m`;
  } else {
    const h = Math.floor(min / 60);
    const m = min % 60;
    timeElapsed.value = `${h}h ${m}m`;
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

const isUrgent = computed(() => {
  if (['completed', 'cancelled', 'done'].includes(props.order.status.toLowerCase())) return false;
  const created = new Date(props.order.created_at).getTime();
  return (Date.now() - created) > 10 * 60 * 1000;
});

const waitMinutes = computed(() => {
  return Math.floor((Date.now() - new Date(props.order.created_at).getTime()) / 60000);
});

const nextAction = computed(() => {
  const s = props.order.status.toLowerCase();
  if (['pending', 'new'].includes(s)) return { label: 'Start', action: 'processing', style: 'bg-primary text-white shadow-primary/25' };
  if (['processing', 'inprogress'].includes(s)) return { label: 'Ready', action: 'completed', style: 'bg-secondary text-secondary-content shadow-secondary/25' };
  return null;
});
</script>

<template>
  <div 
    class="bg-white p-4 rounded-[24px] md:rounded-[28px] shadow-sm border border-gray-100 relative overflow-hidden transition-all duration-400 ease-luxury transform-gpu hover:shadow-md active:scale-[0.98] group"
    :class="{ 'ring-2 ring-red-400/40 shadow-red-100': isUrgent }"
  >
    <!-- Urgent Indicator -->
    <div v-if="isUrgent" class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-400 via-red-500 to-red-400"></div>

    <!-- Header Row -->
    <div class="flex justify-between items-start gap-3 mb-3">
      <!-- Order ID -->
      <div class="flex items-center gap-2">
        <div class="size-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
          <span class="text-lg font-black text-primary">#{{ order.id }}</span>
        </div>
        <div class="flex flex-col">
          <span class="text-sm font-black text-text-main leading-tight">{{ formatTime(order.created_at) }}</span>
          <span class="text-[10px] font-bold text-text-sub" :class="{ 'text-red-500': isUrgent }">{{ timeElapsed }} ago</span>
        </div>
      </div>
      
      <!-- Urgent Badge -->
      <div v-if="isUrgent" class="flex items-center gap-1 bg-red-50 text-red-500 px-2 py-1 rounded-lg">
        <span class="material-symbols-rounded text-sm">priority_high</span>
        <span class="text-[10px] font-black uppercase">{{ waitMinutes }}m</span>
      </div>
    </div>

    <!-- Items List -->
    <div class="space-y-2.5 mb-4">
      <div v-for="(item, i) in order.items" :key="i" class="flex items-center gap-3">
        <!-- Item Image -->
        <div class="size-11 rounded-xl bg-background-light shrink-0 overflow-hidden relative">
          <img v-if="item.image" :src="item.image" class="w-full h-full object-cover" :alt="item.name" />
          <div v-else class="w-full h-full flex items-center justify-center">
            <span class="material-symbols-rounded text-secondary text-lg">local_cafe</span>
          </div>
          <div class="absolute -bottom-0.5 -right-0.5 bg-primary text-white text-[9px] font-bold px-1.5 py-0.5 rounded-tl-lg rounded-br-lg">×{{ item.quantity }}</div>
        </div>

        <!-- Item Info -->
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-text-main leading-tight truncate">{{ item.name }}</p>
          <div class="flex flex-wrap gap-1 mt-1">
            <span v-if="item.temperature" class="inline-flex items-center text-[9px] font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">
              <span class="material-symbols-rounded text-[10px] mr-0.5">{{ item.temperature === 'Hot' ? 'local_fire_department' : 'ac_unit' }}</span>
              {{ item.temperature }}
            </span>
            <span v-if="item.sugar" class="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-600">{{ item.sugar }}</span>
            <span v-if="item.ice" class="text-[9px] font-bold px-1.5 py-0.5 rounded bg-cyan-50 text-cyan-600">{{ item.ice }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Button -->
    <button 
      v-if="nextAction"
      @click="emit('update-status', order.id, nextAction.action)"
      class="w-full py-3 rounded-xl text-sm font-black shadow-lg active:scale-[0.97] transition-all duration-300 flex items-center justify-center gap-2 relative overflow-hidden"
      :class="nextAction.style"
    >
      <span>{{ nextAction.label }}</span>
      <span class="material-symbols-rounded text-lg">arrow_forward</span>
    </button>
    
    <!-- Done State -->
    <div v-else class="w-full py-2.5 rounded-xl bg-emerald-50 text-emerald-600 text-sm font-bold text-center flex items-center justify-center gap-2">
      <span class="material-symbols-rounded filled text-lg">check_circle</span>
      Ready for Pickup
    </div>
  </div>
</template>
