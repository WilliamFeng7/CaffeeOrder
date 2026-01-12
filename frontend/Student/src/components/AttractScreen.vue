<script setup lang="ts">
/**
 * AttractScreen.vue
 * 
 * 吸引屏组件 (Attract Screen Component).
 * 
 * 主要功能 (Core Features):
 * 1. 待机展示 (Idle Display): 在无人操作时循环播放或静置展示，吸引用户点击。
 * 2. 视觉冲击 (Visual Impact): 高清背景图与动态文字效果。
 * 3. 交互入口 (Entry Point): 点击任意位置或按钮进入点餐流程 ( emit 'start' )。
 */

import { computed } from 'vue';
import { TRANSLATIONS } from '../data';
import type { Language } from '../types';

// --- Props & Events ---
const props = defineProps<{
  lang: Language; // 当前语言
}>();

const emit = defineEmits<{
  (e: 'start'): void; // 开始点餐事件
}>();

// 计算属性: 获取翻译
const t = computed(() => TRANSLATIONS[props.lang]);

</script>

<template>
  <div 
    @click="emit('start')"
    class="relative w-full h-full bg-black overflow-hidden group"
  >
    <!-- Background Image -->
    <!-- 背景图片: 咖啡氛围图 -->
    <img 
      src="https://images.unsplash.com/photo-1497935586351-b67a49e012bf?q=80&w=2071&auto=format&fit=crop" 
      class="absolute inset-0 w-full h-full object-cover opacity-80"
      alt="Coffee Ambience"
    />
    
    <!-- Gradient Overlay -->
    <!-- 渐变遮罩: 增强文字可读性 -->
    <div class="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent"></div>

    <!-- Main Content Centered at Bottom -->
    <!-- 主要内容区域 -->
    <div class="absolute inset-0 flex flex-col items-center justify-end pb-24 text-center z-10 px-8">
      <!-- Animated Icon -->
      <div class="mb-12 animate-bounce">
        <div class="size-20 rounded-full bg-primary flex items-center justify-center shadow-[0_0_40px_rgba(249,245,6,0.6)]">
           <span class="material-symbols-rounded text-4xl text-black">touch_app</span>
        </div>
      </div>
      
      <!-- Slogan -->
      <h1 class="text-7xl font-sans font-black text-white mb-8 tracking-tighter leading-tight relative z-20">Freshly Brewed<br/><span class="text-[#DCCA98] italic font-serif">Just For You</span></h1>
      
      <!-- Start Button -->
      <button class="bg-white text-[#103E32] px-16 py-6 rounded-[32px] font-black text-2xl active:bg-[#DCCA98] active:text-[#103E32] active:scale-95 transition-all duration-500 ease-luxury flex items-center gap-3 shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
        {{ t.startOrdering }}
        <span class="material-symbols-rounded text-3xl">arrow_forward</span>
      </button>
    </div>

    <!-- Floating Brand Logo (Top) -->
    <!-- 顶部悬浮品牌标 -->
    <div class="absolute top-12 left-0 w-full flex justify-center">
       <span class="text-white/80 font-bold tracking-[0.3em] uppercase text-sm border border-white/20 px-4 py-2 rounded-full backdrop-blur-md">
          {{ t.downtownCafe }}
       </span>
    </div>
  </div>
</template>
