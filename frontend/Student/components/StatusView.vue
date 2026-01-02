<script setup lang="ts">
/**
 * StatusView.vue
 * 
 * 订单状态反馈视图组件 (Application Status View Component).
 * 
 * 主要功能 (Core Features):
 * 1. 模拟进度 (Simulation): 模拟 "发送中 -> 制作中 -> 下单成功" 的状态流转。
 * 2. 对号动画 (Animations): 完成时显示跳动的绿色对号。
 * 3. 票据展示 (Ticket Display): 显示模拟的取餐号 (A92) 和虚拟的小票样式。
 */

import { ref, computed, onMounted, onUnmounted } from 'vue';
import { TRANSLATIONS } from '../data';
import type { ViewState, Language } from '../types';

// --- Props & Events ---
const props = defineProps<{
  lang: Language; // 当前语言环境
}>();

const emit = defineEmits<{
  (e: 'navigate', view: ViewState): void; // 导航请求 (通常返回首页)
}>();

// --- 状态定义 (State Definitions) ---

// 当前步骤 (1: Sending/发送中, 2: Brewing/制作中, 3: Placed/下单成功)
const step = ref(1);

// 计算属性: 获取翻译
const t = computed(() => TRANSLATIONS[props.lang]);

// --- 生命周期 (Lifecycle) ---

let t1: any; // 定时器引用 1
let t2: any; // 定时器引用 2

/**
 * 组件挂载后启动模拟流程
 * 2秒后进入步骤2 (Brewing)
 * 5秒后进入步骤3 (Placed)
 */
onMounted(() => {
  t1 = setTimeout(() => step.value = 2, 2000);
  t2 = setTimeout(() => step.value = 3, 5000);
});

/**
 * 组件卸载时清除定时器
 * 防止内存泄漏或回调错误。
 */
onUnmounted(() => {
  clearTimeout(t1);
  clearTimeout(t2);
});

</script>

<template>
  <div class="flex flex-col h-full bg-white relative overflow-hidden">
    <!-- Dynamic Angled Background -->
    <!-- 动态背景: 倾斜的绿色色块 -->
    <div class="absolute top-0 left-0 w-full h-1/2 bg-secondary/30 -skew-y-6 transform origin-top-left z-0"></div>

    <div class="relative z-10 flex flex-col items-center justify-center h-full p-8 text-center">
      
      <!-- Status Icon (Animation) -->
      <!-- 状态图标: 制作中闪烁 / 完成时跳动 -->
      <div v-if="step < 3" class="animate-pulse mb-8">
         <div class="size-24 rounded-full bg-primary flex items-center justify-center mx-auto shadow-[0_0_30px_rgba(27,77,62,0.4)]">
            <span class="material-symbols-rounded text-5xl text-white">coffee_maker</span>
         </div>
      </div>
      <div v-else class="mb-8 animate-[bounce_1s]">
         <div class="size-24 rounded-full bg-green-500 text-white flex items-center justify-center mx-auto shadow-lg">
            <span class="material-symbols-rounded text-5xl">check</span>
         </div>
      </div>

      <!-- Status Text -->
      <!-- 状态文本 -->
      <h1 class="text-4xl font-bold text-text-main mb-2">
         {{ step === 1 ? t.sending : step === 2 ? t.brewing : t.placed }}
      </h1>
      <p class="text-text-sub mb-12">{{ t.wait }}</p>

      <!-- Big Ticket (Mockup) -->
      <!-- 模拟小票样式展示取餐号 -->
      <div class="bg-white rounded-3xl shadow-2xl border border-gray-100 p-8 w-full max-w-md relative overflow-hidden">
         <!-- Zigzag Top Border using CSS Gradient -->
         <div class="absolute top-0 left-0 w-full h-3 bg-[repeating-linear-gradient(45deg,transparent,transparent_10px,#1b4d3e_10px,#1b4d3e_20px)]"></div>
         
         <p class="text-sm font-bold text-gray-400 uppercase tracking-widest mb-2">{{ t.pickupNum }}</p>
         <!-- Mock Number -->
         <div class="text-9xl font-black text-text-main tracking-tighter leading-none mb-6">A92</div>
         
         <!-- View Receipt Button (Mock) -->
         <div class="flex items-center justify-center gap-2 text-sm font-medium bg-background-light py-2 rounded-lg text-text-main">
            <span class="material-symbols-rounded text-base">receipt_long</span>
            {{ t.viewReceipt }}
         </div>
      </div>

      <!-- Done Button -->
      <!-- 返回首页按钮 -->
      <button 
         @click="emit('navigate', 'home')"
         class="mt-12 text-text-sub font-bold flex items-center gap-2 px-6 py-3 rounded-full active:bg-background-light active:text-text-main active:scale-90 transition-all duration-500 ease-luxury"
      >
         <span class="material-symbols-rounded">home</span>
         {{ t.backHome }}
      </button>
    </div>
  </div>
</template>
