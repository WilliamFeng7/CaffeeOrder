<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from '../api';
import { useToastStore } from '../stores/toast';

const storeStatus = ref('open');
const bannerMessage = ref('');
const loading = ref(true);
const toast = useToastStore();

const fetchSettings = async () => {
    loading.value = true;
    try {
        const settings = await api.getSettings();
        const status = settings.find((s: any) => s.key === 'store_status');
        if (status) storeStatus.value = status.value;
        
        const banner = settings.find((s: any) => s.key === 'banner_message');
        if (banner) bannerMessage.value = banner.value;
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const saveSetting = async (key: string, value: string) => {
    try {
        await api.updateSetting(key, value);
        toast.success('设置保存成功');
    } catch (e) {
        toast.error('保存设置失败');
    }
};

onMounted(fetchSettings);
</script>

<template>
  <div class="space-y-6 animate-fade-in">
     <h1 class="text-3xl font-black text-primary tracking-tight">系统设置</h1>

     <div class="bg-white rounded-[32px] p-8 border border-gray-100 shadow-sm space-y-8">
         
         <!-- Store Status -->
         <div class="flex items-center justify-between">
             <div>
                 <h3 class="text-xl font-bold text-gray-900">店铺状态</h3>
                 <p class="text-sm text-gray-400 mt-1">控制店铺是否接收新订单。</p>
             </div>
             
             <div class="flex bg-gray-100 p-1 rounded-xl">
                 <button 
                    @click="storeStatus = 'open'; saveSetting('store_status', 'open')"
                    :class="storeStatus === 'open' ? 'bg-green-500 text-white shadow-lg shadow-green-500/30' : 'text-gray-500 hover:text-gray-700'"
                    class="px-6 py-3 rounded-lg font-bold transition-all text-sm"
                 >
                    营业中
                 </button>
                 <button 
                    @click="storeStatus = 'closed'; saveSetting('store_status', 'closed')"
                     :class="storeStatus === 'closed' ? 'bg-red-500 text-white shadow-lg shadow-red-500/30' : 'text-gray-500 hover:text-gray-700'"
                    class="px-6 py-3 rounded-lg font-bold transition-all text-sm"
                 >
                    已打烊
                 </button>
             </div>
         </div>

         <hr class="border-gray-100">

         <!-- Banner Message -->
         <div>
             <h3 class="text-xl font-bold text-gray-900 mb-4">横幅公告</h3>
             <div class="flex gap-4">
                 <input 
                    v-model="bannerMessage" 
                    type="text" 
                    class="flex-1 h-14 bg-gray-50 rounded-2xl px-6 font-bold text-gray-700 outline-none focus:ring-2 focus:ring-primary/20"
                    placeholder="例如：今日特价！"
                 />
                 <button 
                    @click="saveSetting('banner_message', bannerMessage)"
                    class="h-14 px-8 bg-primary text-white rounded-2xl font-bold shadow-lg shadow-primary/20 hover:scale-105 transition-transform"
                 >
                    保存
                 </button>
             </div>
             <p class="text-xs text-gray-400 mt-2 ml-2">此消息将显示在学生端首页（功能待前端实现）。</p>
         </div>

     </div>
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.4s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
