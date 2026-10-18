<script setup lang="ts">
/** 我的：学生卡信息、历史订单和纯前端语言设置。 */
import AppIcon from '@/components/AppIcon.vue';
import AnimatedNumber from '@shared/components/AnimatedNumber.vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
import { ref, computed, watch } from 'vue';
import { TRANSLATIONS } from '../data';
import type { Order, Language, UserProfile } from '../types';
import OrderHistoryList from '../components/OrderHistoryList.vue';
import { useKeepScroll } from '../composables/useKeepScroll';

const props = defineProps<{
  userProfile: UserProfile;
  lang: Language;
  orders: Order[];
}>();

const emit = defineEmits<{ (e: 'set-lang', lang: Language): void }>();
const showHistory = ref(false);
const t = computed(() => TRANSLATIONS[props.lang]);
const { scroller, onScroll } = useKeepScroll();

const balance = computed(() => props.userProfile.balance);
const formatBalance = (n: number) =>
  `¥${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const balanceSize = computed(() => {
  const len = formatBalance(balance.value).length;
  if (len <= 10) return 'text-[44px] md:text-[52px]';
  if (len <= 13) return 'text-[34px] md:text-[42px]';
  return 'text-[26px] md:text-[32px]';
});

const langOptions = [
  { value: 'en' as const, label: 'EN' },
  { value: 'cn' as const, label: '中文' },
];
const langChoice = ref<Language>(props.lang);
watch(() => props.lang, (value) => { langChoice.value = value; });
const setLang = (value: Language) => {
  langChoice.value = value;
  emit('set-lang', value);
};
</script>

<template>
  <div class="relative h-full overflow-hidden">
    <Transition name="push" mode="out-in">
    <OrderHistoryList
      v-if="showHistory"
      :orders="orders"
      :lang="lang"
      @close="showHistory = false"
    />

    <div v-else class="flex flex-col h-full bg-background-light relative">
       <main ref="scroller" @scroll.passive="onScroll" class="profile-content flex-1 min-h-0 overflow-y-auto no-scrollbar px-5 md:px-10 pt-6 md:pt-10 pb-32">
         <div class="max-w-2xl lg:max-w-5xl mx-auto">
         <h1 class="font-serif text-[30px] md:text-[42px] font-normal leading-tight tracking-[-0.015em] text-text-main animate-fade-in">{{ t.profile }}</h1>

         <div class="lg:mt-8 lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:gap-12 lg:items-start">
         <div class="mt-6 lg:mt-0 rounded-card bg-primary text-white p-6 md:p-8 animate-slide-up-content" style="animation-delay: 60ms">
            <div class="min-w-0">
                <p class="eyebrow !text-white/60">{{ t.memberLevel }}</p>
                <h2 class="mt-2 font-serif text-[26px] md:text-[30px] font-normal leading-tight truncate">{{ userProfile.name || '—' }}</h2>
            </div>

            <div class="mt-10 flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
                <div class="min-w-0">
                    <p class="eyebrow !text-white/60">{{ t.balance }}</p>
                    <AnimatedNumber class="mt-2 block font-serif font-normal leading-none break-all" :class="balanceSize" :value="balance" :format="formatBalance" />
                </div>
                <p class="ml-auto text-[11px] tabular-nums tracking-wide text-white/55 text-right break-all max-w-[190px] leading-relaxed">
                  <span class="block">{{ t.studentNo }}</span>
                  <span class="mt-1 block text-[13px] text-white/75">{{ userProfile.studentNo || '—' }}</span>
                </p>
            </div>
         </div>

         <div class="animate-slide-up-content" style="animation-delay: 120ms">
         <div class="mt-10 lg:mt-0 border-y border-line divide-y divide-line">
             <button type="button" @click.stop="showHistory = true" class="press-row w-[calc(100%+24px)] -mx-3 px-3 rounded-tile min-h-[72px] py-4 flex items-center gap-4 text-left">
                <span class="flex-1 min-w-0">
                   <span class="block text-[16px] text-text-main">{{ t.orderHistory }}</span>
                   <span class="block mt-0.5 text-[13px] text-text-sub">{{ t.viewDetailedHistory }}</span>
                </span>
                <AppIcon name="caret-right" weight="light" class="text-lg text-text-sub" />
             </button>

             <div class="w-full min-h-[72px] py-3 flex items-center gap-4">
                <span class="flex-1 min-w-0 text-[16px] text-text-main">{{ t.language }}</span>
                <SlidingTabs :model-value="langChoice" @update:model-value="setLang" :options="langOptions" variant="segment" size="lg" stretch :label="t.language" class="w-[172px]" />
             </div>
         </div>
         <p class="mt-6 text-center lg:text-left text-[12px] text-text-sub">OTIA Café · v3.0</p>
         </div>
         </div>
         </div>
       </main>
    </div>
    </Transition>
  </div>
</template>
