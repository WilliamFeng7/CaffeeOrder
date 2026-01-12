<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { api } from '../api';
import FinanceChart from '../components/charts/FinanceChart.vue';
import PieChart from '../components/charts/PieChart.vue';

const stats = ref<any>({});
const chartData = ref<any>({ line_chart: [], pie_chart: [] });
const transactions = ref<any[]>([]);
const loading = ref(true);
const activeTab = ref<'transactions' | 'deposits'>('transactions');
const page = ref(1);
const dateRange = ref(7); // Default 7 days
let timer: ReturnType<typeof setInterval> | null = null;

const fetchData = async () => {
    // Only show full loading state on first load or manual change
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
    loading.value = true; // Force spinner when changing range
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
</script>

<template>
<div class="space-y-8 animate-fade-in pb-12">
    <!-- Header -->
    <div class="flex justify-between items-end">
        <div>
            <h1 class="text-3xl font-black text-primary tracking-tight">财务分析</h1>
            <p class="text-gray-500 font-medium mt-1">
                实时营收、充值与资金风险概览
            </p>
        </div>
        <div class="flex gap-3">
             <button @click="exportData" class="px-5 py-2.5 bg-white border border-gray-200 text-gray-600 rounded-xl font-bold text-sm hover:bg-gray-50 transition-colors flex items-center gap-2 shadow-sm">
                 <span class="material-symbols-rounded text-lg">download</span>
                 导出
             </button>
             <select v-model="dateRange" class="px-5 py-2.5 bg-[#103E32] text-white rounded-xl font-bold text-sm shadow-lg shadow-primary/20 flex items-center gap-2 outline-none cursor-pointer hover:bg-opacity-90 transition-all">
                 <option :value="1">统计周期：今日</option>
                 <option :value="7">统计周期：近 7 天</option>
                 <option :value="30">统计周期：近 30 天</option>
                 <option :value="90">统计周期：自定义时间</option>
             </select>
        </div>
    </div>

    <!-- Metrics Cards (Sync with Dashboard Styles) -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Revenue -->
        <div class="bg-white p-6 rounded-[28px] border border-gray-100 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
            <div class="flex justify-between items-start mb-4">
                <div class="size-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                    <span class="material-symbols-rounded">payments</span>
                </div>
                <span class="text-[10px] font-black text-gray-300 uppercase tracking-widest">今日营收</span>
            </div>
            <div class="flex items-baseline gap-1">
                 <span class="text-3xl font-black text-primary">¥{{ (stats.today_sales / 100 || 0).toFixed(2) }}</span>
            </div>
            <p class="text-[10px] text-gray-400 font-bold mt-3">已完成订单实收金额</p>
        </div>

        <!-- Deposits -->
        <div class="bg-white p-6 rounded-[28px] border border-gray-100 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
            <div class="flex justify-between items-start mb-4">
                <div class="size-10 rounded-xl bg-green-50 text-green-600 flex items-center justify-center font-bold">
                    <span class="material-symbols-rounded">account_balance_wallet</span>
                </div>
                <span class="text-[10px] font-black text-gray-300 uppercase tracking-widest">今日充值</span>
            </div>
             <div class="flex items-baseline gap-1">
                 <span class="text-3xl font-black text-primary">¥{{ (stats.today_deposits / 100 || 0).toFixed(2) }}</span>
            </div>
             <p class="text-[10px] text-gray-400 font-bold mt-3">用户充值到账金额</p>
        </div>

        <!-- Liability -->
        <div class="bg-red-50 p-6 rounded-[28px] border border-red-100 shadow-sm relative overflow-hidden group">
            <div class="absolute -right-6 -top-6 size-24 bg-red-100 rounded-full blur-2xl opacity-50"></div>
            <div class="flex justify-between items-start mb-4 relative z-10">
                <div class="size-10 rounded-xl bg-white text-red-600 flex items-center justify-center font-bold shadow-sm">
                    <span class="material-symbols-rounded">money_off</span>
                </div>
                <span class="text-[10px] font-black text-red-400 uppercase tracking-widest">待结算余额</span>
            </div>
             <div class="flex items-baseline gap-1 relative z-10">
                 <span class="text-3xl font-black text-red-600">¥{{ (stats.total_liability / 100 || 0).toFixed(2) }}</span>
            </div>
             <p class="text-[10px] text-red-400 font-bold mt-3 relative z-10">用户账户中尚未结算金额（非异常）</p>
        </div>
    </div>

    <!-- Charts Area -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Dual Line Chart -->
        <div class="lg:col-span-2 bg-white p-8 rounded-[36px] border border-gray-100 shadow-sm">
             <div class="flex justify-between items-center mb-8">
                 <h3 class="font-black text-primary text-xl">资金流动趋势（充值 vs 消费）</h3>
                 <div class="flex gap-4">
                     <div class="flex items-center gap-2">
                         <span class="size-3 rounded-full bg-[#10B981]"></span>
                         <span class="text-xs font-bold text-gray-400 uppercase tracking-tighter">充值</span>
                     </div>
                     <div class="flex items-center gap-2">
                         <span class="size-3 rounded-full bg-[#F87171]"></span>
                         <span class="text-xs font-bold text-gray-400 uppercase tracking-tighter">消费</span>
                     </div>
                 </div>
             </div>
             <div class="h-[300px]">
                 <FinanceChart v-if="chartData.line_chart.length > 0" :data="chartData.line_chart" />
                 <div v-else class="h-full flex items-center justify-center text-gray-300 font-bold bg-gray-50/50 rounded-2xl border border-dashed border-gray-200">
                     暂无趋势数据
                 </div>
             </div>
        </div>
        
        <!-- Pie Chart -->
        <div class="bg-white p-8 rounded-[36px] border border-gray-100 shadow-sm">
             <h3 class="font-black text-primary text-xl mb-8">充值额度分布</h3>
             <div class="h-[300px] relative">
                 <PieChart v-if="chartData.pie_chart.length > 0" :data="chartData.pie_chart" />
                 <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-gray-300 font-bold bg-gray-50/50 rounded-2xl border border-dashed border-gray-200 gap-2">
                     <span>暂无充值记录</span>
                     <span class="text-xs font-normal opacity-70">当前统计周期内未产生充值行为</span>
                 </div>
             </div>
        </div>
    </div>

    <!-- Detailed Logs -->
    <div class="bg-white rounded-[36px] border border-gray-100 shadow-sm overflow-hidden mb-12">
        <div class="flex bg-gray-50/50 p-2 gap-2">
            <button 
                @click="handleTabChange('transactions')" 
                class="px-8 py-3.5 text-sm font-black rounded-2xl transition-all flex items-center gap-2"
                :class="activeTab === 'transactions' ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-gray-400 hover:text-primary hover:bg-white'"
            >
                <span class="material-symbols-rounded text-lg">receipt_long</span>
                消费流水
            </button>
            <button 
                @click="handleTabChange('deposits')" 
                class="px-8 py-3.5 text-sm font-black rounded-2xl transition-all flex items-center gap-2"
                :class="activeTab === 'deposits' ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-gray-400 hover:text-primary hover:bg-white'"
            >
                <span class="material-symbols-rounded text-lg">account_balance_wallet</span>
                充值记录
            </button>
        </div>

        <div class="p-0">
             <table class="w-full">
                 <thead>
                     <tr class="text-gray-400 border-b border-gray-100">
                         <th class="py-5 px-8 text-left text-[10px] font-black uppercase tracking-widest">流水号</th>
                         <th class="py-5 px-8 text-left text-[10px] font-black uppercase tracking-widest">用户详情</th>
                         <th class="py-5 px-8 text-left text-[10px] font-black uppercase tracking-widest">金额</th>
                         <th class="py-5 px-8 text-left text-[10px] font-black uppercase tracking-widest">变动后余额</th>
                         <th class="py-5 px-8 text-left text-[10px] font-black uppercase tracking-widest">交易时间</th>
                         <th class="py-5 px-8 text-left text-[10px] font-black uppercase tracking-widest">交易备注</th>
                     </tr>
                 </thead>
                 <tbody class="divide-y divide-gray-50">
                     <tr v-for="row in transactions" :key="row.id" class="hover:bg-gray-50/80 transition-colors group">
                         <td class="py-5 px-8">
                             <span class="text-xs font-bold text-gray-400 font-mono bg-gray-100 px-2 py-1 rounded-md">{{ (row.id || '').substring(0, 10) }}...</span>
                         </td>
                         <td class="py-5 px-8">
                             <div class="flex flex-col">
                                 <span class="text-sm font-black text-primary">{{ row.user_name }}</span>
                                 <span class="text-[10px] text-gray-400 font-bold opacity-0 group-hover:opacity-100 transition-opacity">{{ row.username }}</span>
                             </div>
                         </td>
                         <td class="py-5 px-8">
                             <span :class="row.amount < 0 ? 'text-red-600 bg-red-50' : 'text-green-600 bg-green-50'" class="font-black px-3 py-1 rounded-full text-sm">
                                 {{ row.amount < 0 ? '-' : '+' }}¥ {{ (Math.abs(row.amount)/100).toFixed(2) }}
                             </span>
                         </td>
                         <td class="py-5 px-8 text-sm font-black text-gray-700">¥ {{ (row.balance_after/100).toFixed(2) }}</td>
                         <td class="py-5 px-8">
                             <div class="flex flex-col">
                                 <span class="text-xs font-bold text-gray-600">{{ new Date(row.created_at).toLocaleDateString() }}</span>
                                 <span class="text-[10px] text-gray-400 font-medium">{{ new Date(row.created_at).toLocaleTimeString() }}</span>
                             </div>
                         </td>
                         <td class="py-5 px-8">
                             <span class="text-xs text-gray-500 font-medium max-w-[200px] truncate block">{{ row.description }}</span>
                         </td>
                     </tr>
                     <tr v-if="transactions.length === 0">
                         <td colspan="6" class="py-20 text-center">
                             <div class="flex flex-col items-center gap-2 opacity-20">
                                 <span class="material-symbols-rounded text-6xl">database_off</span>
                                 <p class="font-black text-xl uppercase tracking-widest">暂无记录</p>
                             </div>
                         </td>
                     </tr>
                 </tbody>
             </table>
        </div>
    </div>
</div>
</template>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #E5E7EB;
  border-radius: 10px;
}
</style>
