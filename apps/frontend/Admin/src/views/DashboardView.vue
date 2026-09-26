<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { api, type DashboardStats } from '../api';
import TrendChart from '../components/charts/TrendChart.vue';

const stats = ref<DashboardStats | null>(null);
const loading = ref(true);
const error = ref(false);
let timer: ReturnType<typeof setInterval> | null = null;

const fetchData = async () => {
    // frequent polling shouldn't show loading spinner every time if we already have data
    if (!stats.value) loading.value = true; 
    error.value = false;
    try {
        stats.value = await api.getDashboardStats();
    } catch (e) {
        error.value = true;
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const refreshPage = () => {
    loading.value = true; // Force spinner on manual refresh
    fetchData();
};

onMounted(() => {
    fetchData();
    timer = setInterval(fetchData, 2000); // Poll every 2 seconds
});

onUnmounted(() => {
    if (timer) clearInterval(timer);
});

// Utilities
const formatCurrency = (val: number) => {
    return val.toLocaleString('zh-CN', { style: 'currency', currency: 'CNY' });
};

const formatPercent = (val: number) => {
    return `${val > 0 ? '+' : ''}${val}%`;
};
</script>

<template>
  <div v-if="loading" class="flex items-center justify-center h-[500px]">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
  </div>
  
  <div v-else-if="error" class="flex flex-col items-center justify-center h-[500px] text-center">
      <span class="material-symbols-rounded text-6xl text-red-500 mb-4">error_outline</span>
      <h3 class="text-xl font-bold text-gray-800">加载数据失败</h3>
      <button @click="refreshPage" class="mt-4 px-6 py-2 bg-primary text-white rounded-xl font-bold">重试</button>
  </div>

  <div v-else-if="stats" class="space-y-8 animate-fade-in pb-12">
      <!-- 1. Header & Quick Actions -->
      <div class="flex justify-between items-end">
          <div>
              <h1 class="text-3xl font-black text-primary tracking-tight">运营概览 Dashboard</h1>
              <p class="text-gray-500 font-medium mt-1">
                 实时数据更新于 {{ new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit'}) }}
              </p>
          </div>
          <button @click="refreshPage" class="px-5 py-2.5 bg-white border border-gray-200 text-gray-600 rounded-xl font-bold text-sm hover:bg-gray-50 transition-colors flex items-center gap-2 shadow-sm">
              <span class="material-symbols-rounded text-lg">refresh</span>
              刷新数据
          </button>
      </div>

      <!-- 2. Key Metrics Cards (Top Row) -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <!-- Card 1: Revenue -->
          <div class="bg-white p-5 rounded-[24px] shadow-sm border border-gray-100 relative overflow-hidden group">
              <div class="flex justify-between items-start mb-2">
                  <p class="text-gray-400 font-bold text-xs uppercase tracking-widest">今日营业额</p>
                  <span class="material-symbols-rounded text-primary/20 p-1.5 bg-primary/5 rounded-lg">payments</span>
              </div>
              <h3 class="text-2xl font-black text-primary tracking-tight mb-1">{{ formatCurrency(stats.overview.total_revenue_today) }}</h3>
              <div class="flex items-center gap-1.5">
                   <div class="px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-0.5"
                        :class="stats.overview.revenue_growth >= 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'">
                       <span class="material-symbols-rounded text-sm">{{ stats.overview.revenue_growth >= 0 ? 'trending_up' : 'trending_down' }}</span>
                       {{ formatPercent(stats.overview.revenue_growth) }}
                   </div>
                   <span class="text-[10px] text-gray-400">较昨日</span>
              </div>
          </div>

          <!-- Card 2: Total Orders -->
          <div class="bg-white p-5 rounded-[24px] shadow-sm border border-gray-100 relative overflow-hidden group">
              <div class="flex justify-between items-start mb-2">
                  <p class="text-gray-400 font-bold text-xs uppercase tracking-widest">今日订单量</p>
                  <span class="material-symbols-rounded text-blue-500/20 p-1.5 bg-blue-50 rounded-lg text-blue-600">receipt_long</span>
              </div>
              <h3 class="text-2xl font-black text-primary tracking-tight mb-1">{{ stats.overview.total_orders_today }}</h3>
              <div class="flex items-center gap-1.5">
                   <div class="px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-0.5"
                        :class="stats.overview.orders_growth >= 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'">
                       {{ formatPercent(stats.overview.orders_growth) }}
                   </div>
                   <span class="text-[10px] text-gray-400">较昨日</span>
              </div>
          </div>

          <!-- Card 3: AOV -->
          <div class="bg-white p-5 rounded-[24px] shadow-sm border border-gray-100 relative overflow-hidden group">
              <div class="flex justify-between items-start mb-2">
                  <p class="text-gray-400 font-bold text-xs uppercase tracking-widest">客单价 (AOV)</p>
                  <span class="material-symbols-rounded text-orange-500/20 p-1.5 bg-orange-50 rounded-lg text-orange-600">attach_money</span>
              </div>
              <h3 class="text-2xl font-black text-primary tracking-tight mb-1">{{ formatCurrency(stats.overview.aov_today) }}</h3>
              <div class="flex items-center gap-1.5">
                   <span class="text-[10px] text-gray-400">每单平均消费</span>
              </div>
          </div>

           <!-- Card 4: Pending -->
           <div class="bg-primary text-white p-5 rounded-[24px] shadow-lg shadow-primary/20 relative overflow-hidden group ring-4 ring-primary/5">
              <div class="absolute -right-4 -top-4 size-24 bg-white/10 rounded-full blur-2xl"></div>
              <div class="flex justify-between items-start mb-2 relative z-10">
                  <p class="text-white/60 font-bold text-xs uppercase tracking-widest">当前制作中</p>
                  <span class="material-symbols-rounded text-white/30 p-1.5 bg-white/10 rounded-lg">coffee_maker</span>
              </div>
              <h3 class="text-3xl font-black text-white tracking-tight mb-1 relative z-10">{{ stats.overview.pending_orders_count }}</h3>
              <div class="flex items-center gap-1.5 relative z-10">
                   <div class="px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-0.5 bg-white/20">
                       <span class="material-symbols-rounded text-sm" aria-hidden="true">sync</span>
                       需关注
                   </div>
              </div>
          </div>

          <!-- Card 5: New Members -->
          <div class="bg-white p-5 rounded-[24px] shadow-sm border border-gray-100 relative overflow-hidden group">
              <div class="flex justify-between items-start mb-2">
                  <p class="text-gray-400 font-bold text-xs uppercase tracking-widest">今日新增会员</p>
                  <span class="material-symbols-rounded text-purple-500/20 p-1.5 bg-purple-50 rounded-lg text-purple-600">group_add</span>
              </div>
              <h3 class="text-2xl font-black text-primary tracking-tight mb-1">{{ stats.overview.new_members_today }}</h3>
              <div class="flex items-center gap-1.5">
                   <span class="text-[10px] text-gray-400">累计注册用户</span>
              </div>
          </div>
      </div>

      <!-- 3. Operations Center (Middle Row) -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Left: Real-time Funnel & Wait Time -->
          <div class="bg-white p-6 rounded-[32px] shadow-sm border border-gray-100 flex flex-col gap-6">
              <div class="flex items-center justify-between">
                 <h3 class="text-lg font-black text-primary">实时订单漏斗</h3>
                 <div class="flex items-center gap-2 bg-gray-50 px-3 py-1 rounded-full border border-gray-100">
                    <span class="size-2 rounded-full" :class="stats.operations.estimated_wait_minutes > 15 ? 'bg-red-500 animate-pulse' : 'bg-green-500'"></span>
                    <span class="text-xs font-bold text-gray-500">预计等待 {{ stats.operations.estimated_wait_minutes }} 分钟</span>
                 </div>
              </div>

              <!-- Funnel Steps -->
              <div class="space-y-4 flex-1 justify-center flex flex-col">
                  <!-- Step 1 Pending -->
                  <div class="flex items-center gap-4 group">
                      <div class="size-10 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center font-bold text-lg shadow-sm group-hover:scale-110 transition-transform">
                          {{ stats.operations.funnel.pending }}
                      </div>
                      <div class="flex-1 border-b border-gray-100 pb-2">
                          <p class="font-bold text-gray-800 text-sm">待接单 / 待制作</p>
                          <div class="h-1.5 w-full bg-gray-100 rounded-full mt-1 overflow-hidden">
                              <div class="h-full bg-orange-400 rounded-full" 
                                   :style="{ width: `${Math.max((stats.operations.funnel.pending / (Math.max(stats.operations.funnel.pending + stats.operations.funnel.processing + stats.operations.funnel.ready, 1))) * 100, 5)}%` }"></div>
                          </div>
                      </div>
                  </div>
                  <!-- Step 2 Processing -->
                  <div class="flex items-center gap-4 group">
                      <div class="size-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-lg shadow-sm group-hover:scale-110 transition-transform">
                          {{ stats.operations.funnel.processing }}
                      </div>
                      <div class="flex-1 border-b border-gray-100 pb-2">
                          <p class="font-bold text-gray-800 text-sm">制作中</p>
                          <div class="h-1.5 w-full bg-gray-100 rounded-full mt-1 overflow-hidden">
                              <div class="h-full bg-blue-400 rounded-full" 
                                   :style="{ width: `${Math.max((stats.operations.funnel.processing / (Math.max(stats.operations.funnel.pending + stats.operations.funnel.processing + stats.operations.funnel.ready, 1))) * 100, 5)}%` }"></div>
                          </div>
                      </div>
                  </div>
                  <!-- Step 3 Ready -->
                  <div class="flex items-center gap-4 group">
                      <div class="size-10 rounded-xl bg-green-50 text-green-600 flex items-center justify-center font-bold text-lg shadow-sm group-hover:scale-110 transition-transform">
                          {{ stats.operations.funnel.ready }}
                      </div>
                      <div class="flex-1 border-b border-gray-100 pb-2">
                          <p class="font-bold text-gray-800 text-sm">请取餐</p>
                          <div class="h-1.5 w-full bg-gray-100 rounded-full mt-1 overflow-hidden">
                              <div class="h-full bg-green-400 rounded-full" 
                                   :style="{ width: `${Math.max((stats.operations.funnel.ready / (Math.max(stats.operations.funnel.pending + stats.operations.funnel.processing + stats.operations.funnel.ready, 1))) * 100, 5)}%` }"></div>
                          </div>
                      </div>
                  </div>
                  
                  <!-- Completed/Cancelled Stats Small -->
                  <div class="grid grid-cols-2 gap-4 mt-2">
                      <div class="bg-gray-50 rounded-xl p-3 text-center">
                          <p class="text-[10px] text-gray-400 font-bold uppercase">今日已完成</p>
                          <p class="text-xl font-black text-gray-600">{{ stats.operations.funnel.completed }}</p>
                      </div>
                      <div class="bg-gray-50 rounded-xl p-3 text-center">
                          <p class="text-[10px] text-gray-400 font-bold uppercase">已取消/退单</p>
                          <p class="text-xl font-black text-gray-400">{{ stats.operations.funnel.cancelled }}</p>
                      </div>
                  </div>
              </div>
          </div>

          <!-- Right: Trend Chart -->
          <div class="lg:col-span-2 bg-white p-6 rounded-[32px] shadow-sm border border-gray-100 flex flex-col">
              <div class="flex items-center justify-between mb-6">
                 <h3 class="text-lg font-black text-primary">24小时销售趋势</h3>
                 <div class="flex items-center gap-4 text-xs font-bold text-gray-400">
                     <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-[#103E32]"></span> 订单量</span>
                     <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-[#DCCA98]"></span> 销售额</span>
                 </div>
              </div>
              <div class="flex-1 min-h-[300px]">
                  <TrendChart :data="stats.operations.trend" />
              </div>
          </div>
      </div>

      <!-- 4. Inventory Insights (Bottom Row) -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Top Selling -->
          <div class="bg-[#103E32] rounded-[32px] p-8 text-white relative overflow-hidden">
               <div class="absolute top-0 right-0 -mr-16 -mt-16 size-64 bg-[#DCCA98] rounded-full blur-[100px] opacity-20 pointer-events-none"></div>
               <h3 class="text-xl font-black mb-6 flex items-center gap-2">
                   <span class="material-symbols-rounded text-[#DCCA98]">emoji_events</span>
                   热销商品排行榜 TOP 3
               </h3>
               
               <div class="space-y-4 relative z-10">
                   <div v-if="!stats.inventory.top_selling_items.length" class="text-white/30 text-center py-8 italic font-medium">暂无数据</div>
                   <div v-else v-for="(item, idx) in stats.inventory.top_selling_items" :key="idx" class="flex items-center gap-4">
                       <div class="size-10 rounded-full bg-white/10 text-[#DCCA98] font-black text-xl flex items-center justify-center border border-[#DCCA98]/20">{{ idx + 1 }}</div>
                       <div class="flex-1">
                           <p class="font-bold text-lg">{{ item.name }}</p>
                           <div class="h-1.5 w-full bg-black/20 rounded-full mt-1.5 overflow-hidden">
                               <div class="h-full bg-[#DCCA98]" :style="{ width: `${(item.sales / stats.inventory.top_selling_items[0].sales) * 100}%` }"></div>
                           </div>
                       </div>
                       <div class="text-right">
                           <p class="text-2xl font-black text-white">{{ item.sales }}</p>
                           <p class="text-[10px] text-white/50 font-bold uppercase">已售</p>
                       </div>
                   </div>
               </div>
          </div>

          <!-- Sold Out Alerts -->
          <div class="bg-white rounded-[32px] p-8 shadow-sm border border-gray-100 flex flex-col h-[350px]">
               <div class="flex items-center justify-between mb-4">
                   <h3 class="text-xl font-black text-red-600 flex items-center gap-2">
                       <span class="material-symbols-rounded">warning</span>
                       售罄商品
                   </h3>
                   <span v-if="stats.inventory.sold_out_items.length" class="bg-red-50 text-red-600 px-3 py-1 rounded-full text-xs font-bold">{{ stats.inventory.sold_out_items.length }} Items</span>
               </div>

               <div v-if="!stats.inventory.sold_out_items.length" class="flex-1 flex flex-col items-center justify-center text-gray-400">
                   <span class="material-symbols-rounded text-6xl opacity-20 text-green-500 mb-2">check_circle</span>
                   <p class="font-bold opacity-50">库存充足</p>
               </div>

               <div v-else class="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                   <div v-for="(item, idx) in stats.inventory.sold_out_items" :key="idx" class="flex items-center justify-between p-4 bg-red-50 rounded-2xl border border-red-100">
                       <div>
                           <p class="font-black text-gray-800">{{ item.name }}</p>
                           <p class="text-xs text-red-400 font-bold mt-0.5 uppercase tracking-wider">{{ item.category }}</p>
                       </div>
                       <!-- Placeholder for future functionality -->
                       <button class="text-xs bg-white border border-red-200 text-red-600 px-3 py-1.5 rounded-lg font-bold hover:bg-red-500 hover:text-white transition-colors shadow-sm">
                           补货
                       </button>
                   </div>
               </div>
          </div>
      </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.6s ease-out forwards;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
