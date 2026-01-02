<script setup lang="ts">
import type { Order, Language } from '../types';
import { computed } from 'vue';
import { TRANSLATIONS } from '../data';

const props = defineProps<{
  orders: Order[];
  lang: Language;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const t = computed(() => TRANSLATIONS[props.lang]);

/**
 * 排序后的历史订单 (Sorted History)
 * 按日期降序排列 (最新的在最前)。
 */
const historyOrders = computed(() => {
    return [...props.orders].sort((a, b) => {
        return new Date(b.date).getTime() - new Date(a.date).getTime();
    });
});

/**
 * 格式化日期时间
 * Format: YYYY/MM/DD HH:mm:ss
 */
const formatDate = (dateStr: string) => {
  try {
      const d = new Date(dateStr);
      return d.toLocaleString('zh-CN', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
      });
  } catch (e) {
      return dateStr;
  }
};
</script>

<template>
  <div class="flex flex-col h-full bg-background-light animate-slide-up-content">
     <!-- Header Navigation -->
     <header class="flex items-center p-6 pt-12 sticky top-0 bg-background-light/95 backdrop-blur z-20">
       <button 
           @click="emit('close')" 
           class="flex items-center justify-center size-12 rounded-full bg-white shadow-sm active:scale-90 transition-all font-black"
       >
          <span class="material-symbols-rounded text-text-main">arrow_back</span>
       </button>
       <h1 class="text-2xl font-black ml-4 text-text-main">{{ t.orderHistory }}</h1>
     </header>
     
     <!-- History List -->
     <main class="flex-1 overflow-y-auto p-6 space-y-6 pb-32">
        <!-- Empty State -->
        <div v-if="orders.length === 0" class="h-64 flex flex-col items-center justify-center text-gray-400">
          <span class="material-symbols-rounded text-6xl opacity-20">history</span>
          <p class="mt-4 font-bold">{{ t.noOrders }}</p>
        </div>
        
        <!-- Order Card -->
        <div 
          v-else
          v-for="order in historyOrders" 
          :key="order.id" 
          class="bg-white p-6 rounded-[24px] shadow-sm border border-gray-100" 
        >
            <!-- Order Header Info -->
            <div class="flex justify-between items-start mb-4 pb-4 border-b border-gray-50">
                <div class="space-y-1">
                  <!-- Date -->
                  <p class="text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                      {{ formatDate(order.date) }}
                  </p>
                  <!-- Pickup Number -->
                  <h3 class="text-xl font-black text-primary">#{{ order.dailyNumber }}</h3>
                  
                  <!-- UUIDs for verification -->
                  <div class="flex flex-col gap-0.5 mt-2">
                       <p class="text-[9px] text-gray-400 font-mono">
                           <span class="opacity-50">OID:</span> {{ order.order_no }}
                       </p>
                  </div>
                </div>
                
                <div class="text-right">
                  <!-- Total Price -->
                  <span class="block text-2xl font-black text-text-main">¥{{ order.total.toFixed(2) }}</span>
                  <!-- Status Tag -->
                  <div class="mt-2 flex justify-end">
                    <span 
                        class="px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-wider"
                        :class="order.isCompleted ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'"
                    >
                        {{ order.isCompleted ? t.completed : 'Pending' }}
                    </span>
                  </div>
                </div>
            </div>

            <!-- Order Items List -->
            <div class="space-y-3">
                <div v-for="(item, i) in order.items" :key="i" class="flex items-center gap-3">
                    <div 
                        class="size-12 rounded-xl bg-gray-50 bg-cover bg-center shrink-0" 
                        :style="{ backgroundImage: `url(${item.image})` }"
                    ></div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-black text-text-main truncate">
                            {{ lang === 'cn' ? (item.nameCN || item.name) : item.name }}
                        </p>
                        <p class="text-[10px] text-gray-400 truncate">
                            {{ item.temperature }} · {{ item.sugar }}
                        </p>
                    </div>
                    <span class="text-sm font-bold text-text-main">x{{ item.quantity }}</span>
                </div>
            </div>
        </div>
     </main>
  </div>
</template>
