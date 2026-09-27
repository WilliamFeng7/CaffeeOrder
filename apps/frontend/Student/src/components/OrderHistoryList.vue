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
     <header class="flex items-center gap-2 px-3 md:px-8 pt-5 md:pt-8 pb-3 shrink-0">
       <button
           type="button"
           @click="emit('close')"
           :aria-label="lang === 'cn' ? '返回' : 'Back'"
           class="size-11 rounded-full text-text-main flex items-center justify-center active:bg-cream"
       >
          <AppIcon name="arrow-left" class="text-xl" />
       </button>
       <h1 class="font-serif text-[26px] md:text-[32px] font-medium tracking-[-0.01em] text-text-main">{{ t.orderHistory }}</h1>
     </header>

     <main class="flex-1 overflow-y-auto no-scrollbar px-5 md:px-10 pt-2 pb-32">
        <div class="max-w-2xl mx-auto">
        <div v-if="orders.length === 0" class="py-24 flex flex-col items-center text-text-sub">
          <AppIcon name="history" class="text-3xl mb-3" />
          <p class="text-[15px]">{{ t.noOrders }}</p>
        </div>

        <ul v-else class="divide-y divide-line border-y border-line">
          <li v-for="order in historyOrders" :key="order.id" class="py-5">
            <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="font-serif text-[22px] font-medium text-text-main tabular-nums leading-none">#{{ order.dailyNumber }}</p>
                  <p class="mt-1.5 text-[13px] text-text-sub tabular-nums">{{ formatDate(order.date) }}</p>
                </div>
                <div class="text-right shrink-0">
                  <p class="text-[16px] font-medium text-text-main tabular-nums">¥{{ order.total.toFixed(2) }}</p>
                  <p class="mt-1 text-[12px]" :class="order.isCompleted ? 'text-primary' : 'text-secondary-content'">
                      {{ order.isCompleted ? t.completed : (lang === 'cn' ? '进行中' : 'In progress') }}
                  </p>
                </div>
            </div>

            <div class="mt-3 space-y-2">
                <div v-for="(item, i) in order.items" :key="i" class="flex items-center gap-3">
                    <img v-if="item.image" :src="item.image" alt="" class="size-10 rounded-[10px] object-cover bg-cream shrink-0" loading="lazy" decoding="async" />
                    <p class="flex-1 min-w-0 text-[14px] text-text-main truncate">
                        {{ lang === 'cn' ? (item.nameCN || item.name) : item.name }}
                        <span class="text-text-sub"> · {{ item.temperature }} · {{ item.sugar }}</span>
                    </p>
                    <span class="text-[14px] text-text-sub tabular-nums">×{{ item.quantity }}</span>
                </div>
            </div>
            <p class="mt-3 text-[11px] font-mono text-text-sub truncate">{{ order.order_no }}</p>
          </li>
        </ul>
        </div>
     </main>
  </div>
</template>
