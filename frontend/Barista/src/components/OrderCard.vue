<script setup lang="ts">
import type { Order } from '../api';
import { computed } from 'vue';

const props = defineProps<{
  order: Order;
}>();

const emit = defineEmits<{
  (e: 'update-status', orderId: number, status: string): void;
}>();

// --- Time formatting ---
const formatTime = (isoString: string) => {
  return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
};
const timeElapsed = computed(() => {
    const min = Math.floor((Date.now() - new Date(props.order.created_at).getTime()) / 60000);
    return `${min}m`;
});

// --- Logic ---
const isUrgent = computed(() => {
  if (['completed', 'cancelled', 'done'].includes(props.order.status.toLowerCase())) return false;
  const created = new Date(props.order.created_at).getTime();
  return (Date.now() - created) > 10 * 60 * 1000;
});

const nextAction = computed(() => {
  const s = props.order.status.toLowerCase();
  if (['pending', 'new'].includes(s)) return { label: 'Start', action: 'processing', style: 'bg-primary text-white' };
  if (['processing', 'inprogress'].includes(s)) return { label: 'Ready', action: 'completed', style: 'bg-[#DCCA98] text-[#2C2108]' };
  return null;
});

// Map status to color
const statusColor = computed(() => {
    const s = props.order.status.toLowerCase();
    if (['pending', 'new'].includes(s)) return 'bg-yellow-100 text-yellow-800';
    if (['processing', 'inprogress'].includes(s)) return 'bg-blue-100 text-blue-800';
    if (['completed', 'done'].includes(s)) return 'bg-green-100 text-green-800';
    return 'bg-gray-100 text-gray-500';
});
</script>

<template>
  <div 
    class="bg-white p-6 rounded-[40px] shadow-[0_10px_40px_-10px_rgba(0,0,0,0.05)] border border-white/60 relative overflow-hidden transition-all duration-500 ease-luxury transform-gpu hover:shadow-[0_20px_60px_-15px_rgba(0,0,0,0.1)] hover:-translate-y-1 hover:scale-[1.02] group"
    :class="{ 'ring-4 ring-offset-2 ring-red-500/20': isUrgent }"
  >
    <!-- Background Gradient similar to Student Card -->
    <div class="absolute inset-0 bg-gradient-to-b from-white to-gray-50/50 opacity-50 pointer-events-none"></div>

    <!-- Urgent Marker -->
    <div v-if="isUrgent" class="absolute top-5 right-5 z-20">
        <div class="bg-red-500 text-white text-[10px] font-black px-3 py-1 rounded-full shadow-lg animate-pulse flex items-center gap-1">
            <span class="material-symbols-rounded text-sm">warning</span>
            URGENT
        </div>
    </div>

    <div class="relative z-10">
        <!-- Header -->
        <div class="flex justify-between items-start mb-5 pb-4 border-b border-gray-100">
            <div class="flex flex-col">
                <span class="text-[9px] text-gray-400 font-black uppercase tracking-[0.2em] mb-1">Order #</span>
                <h3 class="text-4xl font-serif font-black text-primary leading-none tracking-tight">#{{ order.id }}</h3>
            </div>
            <div class="flex flex-col items-end gap-1 pt-1">
                 <span class="text-lg font-black text-text-main font-sans tracking-tight">{{ formatTime(order.created_at) }}</span>
                 <span class="text-[9px] font-bold text-gray-400 bg-gray-100 px-2 py-1 rounded-full">{{ timeElapsed }} ago</span>
            </div>
        </div>

        <!-- Items -->
        <div class="space-y-4 min-h-[100px]">
            <div v-for="(item, i) in order.items" :key="i" class="flex items-start gap-4 group/item">
                <!-- Item Image -->
                <div class="size-14 rounded-[20px] bg-gray-50 shrink-0 overflow-hidden shadow-inner relative group-hover/item:scale-105 transition-transform duration-300">
                    <img v-if="item.image" :src="item.image" class="w-full h-full object-cover mix-blend-multiply opacity-90" />
                    <div v-else class="w-full h-full flex items-center justify-center bg-[#F2F7F5]">
                        <span class="material-symbols-rounded text-[#DCCA98] text-2xl">local_cafe</span>
                    </div>
                    <div class="absolute bottom-0 right-0 bg-primary text-white text-[10px] font-bold px-2 py-0.5 rounded-tl-[12px] shadow-sm">x{{ item.quantity }}</div>
                </div>

                <!-- Details -->
                <div class="flex-1 min-w-0 pt-1">
                    <p class="text-base font-black text-text-main leading-tight mb-1.5">{{ item.name }}</p>
                    <div class="flex flex-wrap gap-1.5">
                        <span v-if="item.temperature" class="text-[9px] font-bold px-2 py-0.5 rounded-md bg-gray-100 text-gray-500 uppercase tracking-wide">{{ item.temperature }}</span>
                        <span v-if="item.sugar" class="text-[9px] font-bold px-2 py-0.5 rounded-md bg-gray-100 text-gray-500 uppercase tracking-wide">{{ item.sugar }}</span>
                        <span v-if="item.ice" class="text-[9px] font-bold px-2 py-0.5 rounded-md bg-gray-100 text-gray-500 uppercase tracking-wide">{{ item.ice }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer Actions -->
        <div class="mt-6 pt-0 flex items-center gap-3">
             <!-- Action Button -->
             <button 
                v-if="nextAction"
                @click="emit('update-status', order.id, nextAction.action)"
                class="w-full py-4 rounded-[24px] text-sm font-black shadow-lg shadow-black/5 active:scale-95 transition-all duration-300 flex items-center justify-center gap-2 group-hover:scale-[1.02] relative overflow-hidden"
                :class="nextAction.style"
             >
                <!-- Shimmer effect -->
                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent skew-x-12 translate-x-[-200%] group-hover:animate-shimmer"></div>
                
                <span class="relative z-10">{{ nextAction.label }}</span>
                <span class="material-symbols-rounded text-xl relative z-10">arrow_forward</span>
             </button>
             
             <!-- Completion Badge if no action -->
             <div v-else class="w-full py-3 rounded-[24px] bg-gray-50 text-gray-400 text-sm font-black text-center flex items-center justify-center gap-2">
                <span class="material-symbols-rounded">check_circle</span>
                Done
             </div>
        </div>
    </div>
  </div>
</template>
