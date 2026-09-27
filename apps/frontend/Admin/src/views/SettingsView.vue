<script setup lang="ts">
import { ref, onMounted } from 'vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
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

const statusOptions = [
    { value: 'open', label: '营业中' },
    { value: 'closed', label: '已打烊' },
];
const setStatus = (value: string) => {
    storeStatus.value = value;
    saveSetting('store_status', value);
};

onMounted(fetchSettings);
</script>

<template>
  <div class="space-y-6 max-w-3xl">
     <div class="animate-slide-up-content">
         <p class="eyebrow">店铺</p>
         <h1 class="mt-2 font-serif text-[34px] font-medium leading-tight tracking-[-0.015em]">系统设置</h1>
     </div>

     <section class="card divide-y divide-line animate-slide-up-content" style="animation-delay: 60ms">
         <!-- Store status -->
         <div class="p-6 flex flex-wrap items-center justify-between gap-4">
             <div>
                 <h3 class="text-[15px] font-medium flex items-center gap-2">
                     店铺状态
                     <span class="size-1.5 rounded-full transition-colors duration-color" :class="storeStatus === 'open' ? 'bg-primary' : 'bg-danger'" aria-hidden="true"></span>
                 </h3>
                 <p class="mt-1 text-[13px] text-text-sub">控制店铺是否接收新订单。</p>
             </div>
             <SlidingTabs :model-value="storeStatus" @update:model-value="setStatus" :options="statusOptions" variant="segment" size="sm" label="店铺状态" />
         </div>

         <!-- Banner -->
         <div class="p-6">
             <h3 class="text-[15px] font-medium">横幅公告</h3>
             <div class="mt-4 flex gap-3">
                 <input v-model="bannerMessage" type="text" class="field flex-1" placeholder="例如：今日特价！" />
                 <button type="button" @click="saveSetting('banner_message', bannerMessage)" class="btn btn-primary">保存</button>
             </div>
             <p class="mt-2 text-[12px] text-text-sub">此消息将显示在学生端首页（功能待前端实现）。</p>
         </div>
     </section>
  </div>
</template>
