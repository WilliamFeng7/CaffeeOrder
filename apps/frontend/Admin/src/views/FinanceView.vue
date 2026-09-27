<script setup lang="ts">
/**
 * FinanceView.vue
 *
 * 财务分析: today's sales / top-ups / outstanding balances, money in vs money
 * spent over the chosen period, how top-ups are distributed by amount, and the
 * ledger. Polls every 2 seconds.
 *
 * Motion: numbers count to new values, distribution bars grow, the period and
 * ledger switches slide their indicator and crossfade the table.
 */
import AppIcon from '@shared/components/AppIcon.vue';
import AnimatedNumber from '@shared/components/AnimatedNumber.vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
import { vReveal } from '@shared/reveal';
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { api } from '../api';
import FinanceChart from '../components/charts/FinanceChart.vue';

const stats = ref<any>({});
const chartData = ref<any>({ line_chart: [], pie_chart: [] });
const transactions = ref<any[]>([]);
const loading = ref(true);
const activeTab = ref<'transactions' | 'deposits'>('transactions');
const page = ref(1);
const dateRange = ref(7); // Default 7 days
let timer: ReturnType<typeof setInterval> | null = null;

const rangeOptions = [
    { value: 1, label: '今日' },
    { value: 7, label: '7 天' },
    { value: 30, label: '30 天' },
    { value: 90, label: '90 天' },
];

const ledgerOptions = [
    { value: 'transactions' as const, label: '消费流水' },
    { value: 'deposits' as const, label: '充值记录' },
];

const fetchData = async () => {
    // Only show the full loading state on first load or a manual change
    if (!stats.value.total_liability) loading.value = true;
    try {
        const [s, c, t] = await Promise.all([
            api.getFinanceStats(),
            api.getFinanceChart(dateRange.value),
            api.getFinanceTransactions(page.value, activeTab.value === 'transactions' ? 'order' : 'deposit')
        ]);
        stats.value = s;
        chartData.value = c;
        transactions.value = t;
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

watch(dateRange, () => {
    loading.value = true;
    fetchData();
});

const handleTabChange = (tab: 'transactions' | 'deposits') => {
    activeTab.value = tab;
    page.value = 1;
    fetchData();
};

const exportData = () => {
    const headers = ['ID', 'User', 'Amount', 'BalanceAfter', 'Time', 'Description'];
    const rows = transactions.value.map(t => [
        t.id, t.username, t.amount/100, t.balance_after/100, t.created_at, t.description
    ]);

    let csvContent = "data:text/csv;charset=utf-8,"
        + headers.join(",") + "\n"
        + rows.map(e => e.join(",")).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `finance_report_${activeTab.value}.csv`);
    document.body.appendChild(link);
    link.click();
};

onMounted(() => {
    fetchData();
    timer = setInterval(fetchData, 2000); // Auto-refresh every 2 seconds
});

onUnmounted(() => {
    if (timer) clearInterval(timer);
});

const yuan = (n: number) => `¥${n.toFixed(2)}`;

// Top-ups by amount (ordered by amount), as bars rather than pie slices:
// lengths compare more accurately than angles, and custom amounts can add
// many small categories.
const distribution = computed(() => {
    const rows: Array<{ name: string; value: number }> = chartData.value.pie_chart ?? [];
    const total = rows.reduce((sum, r) => sum + r.value, 0) || 1;
    const max = Math.max(1, ...rows.map(r => r.value));
    return rows.map(r => ({ ...r, share: r.value / total, length: r.value / max }));
});
</script>

<template>
<div class="space-y-6 pb-4">
    <!-- Header -->
    <div class="flex flex-wrap items-end justify-between gap-4 animate-slide-up-content">
        <div>
            <p class="eyebrow">营收 · 充值 · 资金</p>
            <h1 class="mt-2 font-serif text-[34px] font-medium leading-tight tracking-[-0.015em]">财务分析</h1>
        </div>
        <div class="flex items-center gap-3">
            <SlidingTabs v-model="dateRange" :options="rangeOptions" variant="segment" size="sm" label="统计周期" />
            <button type="button" @click="exportData" class="btn btn-outline btn-sm">
                <AppIcon name="download" weight="light" class="text-base" />
                导出
            </button>
        </div>
    </div>

    <!-- Key numbers -->
    <section class="card grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-line animate-slide-up-content" style="animation-delay: 60ms">
        <div class="p-6">
            <p class="eyebrow">今日营收</p>
            <AnimatedNumber class="mt-3 block font-serif text-[30px] font-medium leading-none" :value="(stats.today_sales || 0) / 100" :format="yuan" />
            <p class="mt-3 text-[12px] text-text-sub">已完成订单实收金额</p>
        </div>
        <div class="p-6">
            <p class="eyebrow">今日充值</p>
            <AnimatedNumber class="mt-3 block font-serif text-[30px] font-medium leading-none" :value="(stats.today_deposits || 0) / 100" :format="yuan" />
            <p class="mt-3 text-[12px] text-text-sub">用户充值到账金额</p>
        </div>
        <div class="p-6">
            <p class="eyebrow">待结算余额</p>
            <AnimatedNumber class="mt-3 block font-serif text-[30px] font-medium leading-none" :value="(stats.total_liability || 0) / 100" :format="yuan" />
            <p class="mt-3 text-[12px] text-text-sub">用户账户中尚未消费的金额（非异常）</p>
        </div>
    </section>

    <!-- Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section class="lg:col-span-2 card p-6 animate-slide-up-content" style="animation-delay: 120ms">
             <div class="flex items-center justify-between gap-4">
                 <h3 class="text-[15px] font-medium">资金流动</h3>
                 <div class="flex items-center gap-5 text-[12px] text-text-sub">
                     <span class="flex items-center gap-2"><span class="w-4 h-[2px] rounded-full bg-primary"></span>充值</span>
                     <span class="flex items-center gap-2"><span class="w-4 h-[2px] rounded-full bg-secondary"></span>消费</span>
                 </div>
             </div>
             <div class="mt-6 h-[300px]">
                 <FinanceChart v-if="chartData.line_chart.length > 0" :data="chartData.line_chart" />
                 <div v-else class="h-full flex items-center justify-center text-[13px] text-text-sub rounded-tile border border-dashed border-line">
                     暂无趋势数据
                 </div>
             </div>
        </section>

        <section class="card p-6 flex flex-col animate-slide-up-content" style="animation-delay: 180ms">
             <h3 class="text-[15px] font-medium">充值额度分布</h3>
             <ul v-if="distribution.length" class="mt-6 space-y-5 flex-1">
                 <li v-for="(row, i) in distribution" :key="row.name">
                     <div class="flex items-baseline justify-between gap-3">
                         <span class="font-serif text-[17px] font-medium tabular-nums">{{ row.name }}</span>
                         <span class="text-[12px] text-text-sub tabular-nums">
                             <AnimatedNumber :value="row.value" /> 笔 · {{ Math.round(row.share * 100) }}%
                         </span>
                     </div>
                     <div class="mt-2 h-1 rounded-full bg-line overflow-hidden">
                         <div
                             class="h-full rounded-full bg-primary grow-x transition-transform duration-spring-soft ease-spring-soft"
                             :style="{ transform: `scaleX(${row.length})`, animationDelay: `${300 + i * 80}ms` }"
                         ></div>
                     </div>
                 </li>
             </ul>
             <div v-else class="mt-6 flex-1 min-h-[240px] flex flex-col items-center justify-center gap-1 text-center rounded-tile border border-dashed border-line">
                 <span class="text-[13px] text-text-sub">暂无充值记录</span>
                 <span class="text-[12px] text-text-sub/70">当前统计周期内未产生充值</span>
             </div>
        </section>
    </div>

    <!-- Ledger -->
    <section v-reveal class="card overflow-hidden">
        <div class="px-6 pt-3 border-b border-line">
            <SlidingTabs :model-value="activeTab" @update:model-value="handleTabChange" :options="ledgerOptions" label="流水类型" />
        </div>

        <div class="overflow-x-auto quiet-scrollbar">
            <Transition name="page" mode="out-in">
             <table :key="activeTab" class="w-full text-left">
                 <thead>
                     <tr class="border-b border-line">
                         <th class="py-3.5 px-6 eyebrow font-medium">流水号</th>
                         <th class="py-3.5 px-6 eyebrow font-medium">用户</th>
                         <th class="py-3.5 px-6 eyebrow font-medium text-right">金额</th>
                         <th class="py-3.5 px-6 eyebrow font-medium text-right">变动后余额</th>
                         <th class="py-3.5 px-6 eyebrow font-medium">时间</th>
                         <th class="py-3.5 px-6 eyebrow font-medium">备注</th>
                     </tr>
                 </thead>
                 <tbody class="stagger-in">
                     <tr v-for="row in transactions" :key="row.id" class="border-b border-line last:border-0 hover:bg-background-light transition-colors duration-color">
                         <td class="py-4 px-6">
                             <span class="font-mono text-[12px] text-text-sub" :title="row.id">{{ (row.id || '').substring(0, 10) }}…</span>
                         </td>
                         <td class="py-4 px-6">
                             <p class="text-[14px] font-medium">{{ row.user_name }}</p>
                             <p class="text-[12px] text-text-sub">{{ row.username }}</p>
                         </td>
                         <td class="py-4 px-6 text-right">
                             <span class="font-serif text-[16px] font-medium tabular-nums" :class="row.amount < 0 ? 'text-text-main' : 'text-primary'">
                                 {{ row.amount < 0 ? '−' : '+' }}¥{{ (Math.abs(row.amount)/100).toFixed(2) }}
                             </span>
                         </td>
                         <td class="py-4 px-6 text-right text-[14px] tabular-nums text-text-sub">¥{{ (row.balance_after/100).toFixed(2) }}</td>
                         <td class="py-4 px-6 whitespace-nowrap">
                             <p class="text-[13px] tabular-nums">{{ new Date(row.created_at).toLocaleDateString() }}</p>
                             <p class="text-[12px] text-text-sub tabular-nums">{{ new Date(row.created_at).toLocaleTimeString() }}</p>
                         </td>
                         <td class="py-4 px-6">
                             <span class="text-[13px] text-text-sub max-w-[220px] truncate block">{{ row.description }}</span>
                         </td>
                     </tr>
                     <tr v-if="transactions.length === 0">
                         <td colspan="6" class="py-20 text-center">
                             <div class="flex flex-col items-center gap-2 text-text-sub">
                                 <AppIcon name="database" weight="light" class="text-3xl" />
                                 <p class="text-[13px]">暂无记录</p>
                             </div>
                         </td>
                     </tr>
                 </tbody>
             </table>
            </Transition>
        </div>
    </section>
</div>
</template>
