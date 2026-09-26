<script setup lang="ts">
import AppIcon from '@shared/components/AppIcon.vue';
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
  } catch {
      return dateStr;
  }
};
</script>

<template>
  <div class="flex flex-col h-full bg-background-light animate-fade-in">
     <header class="flex items-center gap-3 px-4 md:px-8 pt-6 md:pt-8 pb-3 shrink-0">
       <button
           type="button"
           @click="emit('close')"
           :aria-label="lang === 'cn' ? '返回' : 'Back'"
           class="size-11 rounded-full bg-white shadow-card text-text-main flex items-center justify-center active:bg-cream/70"
       >
          <AppIcon name="arrow-left" class="text-xl" />
       </button>
       <h1 class="font-display text-[24px] md:text-3xl font-bold tracking-tight text-text-main">{{ t.orderHistory }}</h1>
     </header>

     <main class="flex-1 overflow-y-auto no-scrollbar px-4 md:px-8 pt-2 pb-32">
        <div class="max-w-2xl mx-auto space-y-3">
        <div v-if="orders.length === 0" class="py-24 flex flex-col items-center text-text-sub">
          <AppIcon name="history" class="text-4xl mb-3 opacity-60" />
          <p class="text-[15px] font-medium">{{ t.noOrders }}</p>
        </div>

        <article
          v-else
          v-for="order in historyOrders"
          :key="order.id"
          class="bg-white rounded-card shadow-card p-4"
        >
            <div class="flex items-start justify-between gap-3 pb-3 mb-3 border-b border-line">
                <div class="min-w-0">
                  <p class="text-[12px] text-text-sub tabular-nums">{{ formatDate(order.date) }}</p>
                  <p class="font-display text-xl font-bold text-primary tabular-nums">#{{ order.dailyNumber }}</p>
                  <p class="text-[11px] text-text-sub font-mono truncate">{{ order.order_no }}</p>
                </div>
                <div class="text-right shrink-0">
                  <p class="text-lg font-bold text-text-main tabular-nums">¥{{ order.total.toFixed(2) }}</p>
                  <span
                      class="mt-1 inline-flex h-6 px-2 items-center rounded-full text-[12px] font-semibold"
                      :class="order.isCompleted ? 'bg-primary-soft text-primary' : 'bg-secondary-soft text-secondary-content'"
                  >
                      {{ order.isCompleted ? t.completed : (lang === 'cn' ? '进行中' : 'In progress') }}
                  </span>
                </div>
            </div>

            <div class="space-y-2.5">
                <div v-for="(item, i) in order.items" :key="i" class="flex items-center gap-3">
                    <img v-if="item.image" :src="item.image" alt="" class="size-11 rounded-[10px] object-cover bg-cream shrink-0" loading="lazy" decoding="async" />
                    <div class="flex-1 min-w-0">
                        <p class="text-[14px] font-medium text-text-main truncate">
                            {{ lang === 'cn' ? (item.nameCN || item.name) : item.name }}
                        </p>
                        <p class="text-[12px] text-text-sub truncate">
                            {{ item.temperature }} · {{ item.sugar }}
                        </p>
                    </div>
                    <span class="text-[14px] font-semibold text-text-main tabular-nums">×{{ item.quantity }}</span>
                </div>
            </div>
        </article>
        </div>
     </main>
  </div>
</template>
