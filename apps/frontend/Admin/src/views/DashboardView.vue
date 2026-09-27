<script setup lang="ts">
/**
 * DashboardView.vue
 *
 * 经营概览: today's numbers, the live order funnel, the 24h trend, best
 * sellers and sold-out items. Polls every 2 seconds.
 *
 * Motion: numbers count up on first load and count to new values when they
 * change; bars grow in and glide to new lengths; lower sections rise in as
 * they scroll into view.
 */
import AppIcon from '@shared/components/AppIcon.vue';
import AnimatedNumber from '@shared/components/AnimatedNumber.vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
import { vReveal } from '@shared/reveal';
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { api, type DashboardStats } from '../api';
import TrendChart from '../components/charts/TrendChart.vue';

const stats = ref<DashboardStats | null>(null);
const loading = ref(true);
const error = ref(false);
const updatedAt = ref('');
let timer: ReturnType<typeof setInterval> | null = null;

const fetchData = async () => {
    // Polling must not flash a spinner once there is data on screen.
    if (!stats.value) loading.value = true;
    error.value = false;
    try {
        stats.value = await api.getDashboardStats();
        updatedAt.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) {
        error.value = true;
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const refreshing = ref(false);
const refreshPage = async () => {
    refreshing.value = true;
    await fetchData();
    refreshing.value = false;
};

onMounted(() => {
    fetchData();
    timer = setInterval(fetchData, 2000); // Poll every 2 seconds
});

onUnmounted(() => {
    if (timer) clearInterval(timer);
});

// Utilities
const money = (val: number) => val.toLocaleString('zh-CN', { style: 'currency', currency: 'CNY' });
const percent = (val: number) => `${val > 0 ? '+' : ''}${val}%`;

const funnel = computed(() => {
    const f = stats.value?.operations.funnel;
    if (!f) return [];
    const total = Math.max(f.pending + f.processing + f.ready, 1);
    return [
        { label: '待接单 / 待制作', value: f.pending, share: f.pending / total },
        { label: '制作中', value: f.processing, share: f.processing / total },
        { label: '请取餐', value: f.ready, share: f.ready / total },
    ];
});

const topSales = computed(() => stats.value?.inventory.top_selling_items[0]?.sales || 1);

// Orders and revenue have different units: one at a time, on one axis.
const trendMetric = ref<'orders' | 'revenue'>('orders');
const trendOptions = [
    { value: 'orders' as const, label: '订单量' },
    { value: 'revenue' as const, label: '销售额' },
];
</script>

<template>
  <div v-if="loading" class="flex items-center justify-center h-[480px]">
      <div class="size-8 rounded-full border-[1.5px] border-line border-t-text-main animate-spin" aria-label="加载中"></div>
  </div>

  <div v-else-if="error && !stats" class="flex flex-col items-center justify-center h-[480px] text-center animate-fade-in">
      <AppIcon name="warning-circle" weight="light" class="text-4xl text-danger mb-4" />
      <h3 class="font-serif text-[22px] font-medium">加载数据失败</h3>
      <button type="button" @click="refreshPage" class="btn btn-outline btn-sm mt-5">重试</button>
  </div>

  <div v-else-if="stats" class="space-y-6 pb-4">
      <!-- Title -->
      <div class="flex items-end justify-between gap-4 animate-slide-up-content">
          <div>
              <p class="eyebrow flex items-center gap-2">
                  <span class="relative flex size-1.5">
                      <span :key="updatedAt" class="absolute inset-0 rounded-full bg-primary ping" aria-hidden="true"></span>
                      <span class="relative size-1.5 rounded-full bg-primary" aria-hidden="true"></span>
                  </span>
                  实时 · 更新于 {{ updatedAt }}
              </p>
              <h1 class="mt-2 font-serif text-[34px] font-medium leading-tight tracking-[-0.015em]">经营概览</h1>
          </div>
          <button type="button" @click="refreshPage" class="btn btn-outline btn-sm">
              <AppIcon name="refresh" weight="light" class="text-base" :class="{ 'animate-spin': refreshing }" />
              刷新
          </button>
      </div>

      <!-- Key numbers: one card, hairline dividers -->
      <section class="card grid grid-cols-2 lg:grid-cols-5 animate-slide-up-content [&>*]:border-line max-lg:[&>*:nth-child(n+3)]:border-t max-lg:[&>*:nth-child(even)]:border-l lg:divide-x lg:divide-line" style="animation-delay: 60ms">
          <div class="p-6">
              <p class="eyebrow">今日营业额</p>
              <AnimatedNumber class="mt-3 block font-serif text-[28px] font-medium leading-none" :value="stats.overview.total_revenue_today" :format="money" />
              <p class="mt-3 flex items-center gap-1 text-[12px]" :class="stats.overview.revenue_growth >= 0 ? 'text-primary' : 'text-danger'">
                  <AppIcon :name="stats.overview.revenue_growth >= 0 ? 'trend-up' : 'trend-down'" class="text-sm" />
                  {{ percent(stats.overview.revenue_growth) }}
                  <span class="text-text-sub">较昨日</span>
              </p>
          </div>
          <div class="p-6">
              <p class="eyebrow">今日订单</p>
              <AnimatedNumber class="mt-3 block font-serif text-[28px] font-medium leading-none" :value="stats.overview.total_orders_today" />
              <p class="mt-3 flex items-center gap-1 text-[12px]" :class="stats.overview.orders_growth >= 0 ? 'text-primary' : 'text-danger'">
                  <AppIcon :name="stats.overview.orders_growth >= 0 ? 'trend-up' : 'trend-down'" class="text-sm" />
                  {{ percent(stats.overview.orders_growth) }}
                  <span class="text-text-sub">较昨日</span>
              </p>
          </div>
          <div class="p-6">
              <p class="eyebrow">客单价</p>
              <AnimatedNumber class="mt-3 block font-serif text-[28px] font-medium leading-none" :value="stats.overview.aov_today" :format="money" />
              <p class="mt-3 text-[12px] text-text-sub">每单平均消费</p>
          </div>
          <div class="p-6">
              <p class="eyebrow">当前制作中</p>
              <p class="mt-3 flex items-baseline gap-2">
                  <AnimatedNumber class="font-serif text-[28px] font-medium leading-none" :value="stats.overview.pending_orders_count" />
                  <span v-if="stats.overview.pending_orders_count > 0" class="size-1.5 rounded-full bg-secondary animate-pulse self-center" aria-hidden="true"></span>
              </p>
              <p class="mt-3 text-[12px] text-text-sub">进行中的订单</p>
          </div>
          <div class="p-6 max-lg:col-span-2 max-lg:!border-l-0">
              <p class="eyebrow">今日新增会员</p>
              <AnimatedNumber class="mt-3 block font-serif text-[28px] font-medium leading-none" :value="stats.overview.new_members_today" />
              <p class="mt-3 text-[12px] text-text-sub">注册用户</p>
          </div>
      </section>

      <!-- Operations -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Live funnel -->
          <section class="card p-6 flex flex-col animate-slide-up-content" style="animation-delay: 120ms">
              <div class="flex items-center justify-between gap-3">
                 <h3 class="text-[15px] font-medium">实时订单</h3>
                 <span class="text-[12px] flex items-center gap-1.5" :class="stats.operations.estimated_wait_minutes > 15 ? 'text-danger' : 'text-text-sub'">
                    <span class="dot" aria-hidden="true"></span>
                    预计等待 {{ stats.operations.estimated_wait_minutes }} 分钟
                 </span>
              </div>

              <div class="mt-7 space-y-6 flex-1">
                  <div v-for="step in funnel" :key="step.label">
                      <div class="flex items-baseline justify-between gap-3">
                          <span class="text-[13px] text-text-sub">{{ step.label }}</span>
                          <AnimatedNumber class="font-serif text-[22px] font-medium leading-none" :value="step.value" />
                      </div>
                      <div class="mt-2.5 h-1 rounded-full bg-line overflow-hidden">
                          <div
                              class="h-full rounded-full bg-text-main grow-x transition-transform duration-spring-soft ease-spring-soft"
                              :style="{ transform: `scaleX(${Math.max(step.share, 0.02)})` }"
                          ></div>
                      </div>
                  </div>
              </div>

              <div class="mt-7 pt-5 border-t border-line grid grid-cols-2 gap-4">
                  <div>
                      <p class="eyebrow">今日已完成</p>
                      <AnimatedNumber class="mt-1.5 block font-serif text-[20px] font-medium" :value="stats.operations.funnel.completed" />
                  </div>
                  <div>
                      <p class="eyebrow">已取消 / 退单</p>
                      <AnimatedNumber class="mt-1.5 block font-serif text-[20px] font-medium text-text-sub" :value="stats.operations.funnel.cancelled" />
                  </div>
              </div>
          </section>

          <!-- 24h trend -->
          <section class="lg:col-span-2 card p-6 flex flex-col animate-slide-up-content" style="animation-delay: 180ms">
              <div class="flex items-center justify-between gap-4">
                 <h3 class="text-[15px] font-medium">24 小时趋势</h3>
                 <SlidingTabs v-model="trendMetric" :options="trendOptions" variant="segment" size="sm" label="趋势指标" />
              </div>
              <div class="mt-6 flex-1 min-h-[300px]">
                  <TrendChart :data="stats.operations.trend" :metric="trendMetric" />
              </div>
          </section>
      </div>

      <!-- Inventory -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Best sellers -->
          <section v-reveal class="card p-6">
               <h3 class="text-[15px] font-medium">热销排行</h3>
               <div v-if="!stats.inventory.top_selling_items.length" class="py-12 text-center text-[13px] text-text-sub">暂无数据</div>
               <ol v-else class="mt-6 space-y-6">
                   <li v-for="(item, idx) in stats.inventory.top_selling_items" :key="item.name">
                       <div class="flex items-baseline gap-4">
                           <span class="w-6 font-serif text-[15px] text-text-sub tabular-nums">{{ String(idx + 1).padStart(2, '0') }}</span>
                           <span class="flex-1 min-w-0 truncate text-[15px] font-medium">{{ item.name }}</span>
                           <AnimatedNumber class="font-serif text-[20px] font-medium" :value="item.sales" />
                           <span class="text-[12px] text-text-sub">已售</span>
                       </div>
                       <div class="mt-2.5 ml-10 h-1 rounded-full bg-line overflow-hidden">
                           <div
                               class="h-full rounded-full bg-primary grow-x transition-transform duration-spring-soft ease-spring-soft"
                               :style="{ transform: `scaleX(${item.sales / topSales})`, animationDelay: `${300 + idx * 90}ms` }"
                           ></div>
                       </div>
                   </li>
               </ol>
          </section>

          <!-- Sold out -->
          <section v-reveal="80" class="card p-6 flex flex-col h-[340px]">
               <div class="flex items-center justify-between gap-3">
                   <h3 class="text-[15px] font-medium">售罄商品</h3>
                   <span v-if="stats.inventory.sold_out_items.length" class="chip chip-danger">{{ stats.inventory.sold_out_items.length }} 款</span>
               </div>

               <div v-if="!stats.inventory.sold_out_items.length" class="flex-1 flex flex-col items-center justify-center gap-2 text-text-sub">
                   <AppIcon name="check-circle" weight="light" class="text-3xl text-primary" />
                   <p class="text-[13px]">库存充足</p>
               </div>

               <ul v-else class="mt-4 flex-1 overflow-y-auto quiet-scrollbar divide-y divide-line">
                   <li v-for="item in stats.inventory.sold_out_items" :key="item.name" class="py-3.5 flex items-center justify-between gap-4">
                       <div class="min-w-0">
                           <p class="text-[14px] font-medium truncate">{{ item.name }}</p>
                           <p class="mt-0.5 eyebrow !text-[10px]">{{ item.category }}</p>
                       </div>
                       <router-link to="/products" class="btn btn-outline btn-sm">补货</router-link>
                   </li>
               </ul>
          </section>
      </div>
  </div>
</template>
