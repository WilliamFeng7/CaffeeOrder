<script setup lang="ts">
/**
 * SettingsView.vue
 *
 * 设置与个人中心视图组件 (Settings & Profile View).
 *
 * Motion: the balance counts up when the page is first shown and Order
 * history slides in from the right. The rows themselves stay still (a page
 * visited every day does not re-perform itself).
 */

import AppIcon from '@/components/AppIcon.vue';
import AnimatedNumber from '@shared/components/AnimatedNumber.vue';
import SlidingTabs from '@shared/components/SlidingTabs.vue';
import { ref, computed, watch } from 'vue';
import { TRANSLATIONS } from '../data';
import type { Order, Language, UserProfile } from '../types';
import { useToastStore } from '../stores/toast';

// 导入提取的子组件
import OrderHistoryList from '../components/OrderHistoryList.vue';
import BottomSheet from '../components/BottomSheet.vue';
import PasswordModal from '../components/PasswordModal.vue';
import { useKeepScroll } from '../composables/useKeepScroll';
import { auth } from '@shared/auth';
import { demoMode } from '../demo';

// --- Props & Emits 定义 ---

const props = defineProps<{
  userProfile: UserProfile; // 用户资料对象
  lang: Language;           // 当前语言
  orders: Order[];          // 订单列表数据
}>();

const emit = defineEmits<{
  (e: 'update-profile', profile: UserProfile): void; // 更新资料事件
  (e: 'toggle-lang'): void;                          // 切换语言事件
}>();

// --- 状态变量 (State Variables) ---

const showHistory = ref(false);
const showPasswordModal = ref(false);
const isEditing = ref(false);
const toast = useToastStore();

// 编辑表单数据绑定
const editForm = ref<UserProfile>({
    name: '',
    phone: '',
    email: '',
    avatar: '',
    uuid: ''
});

// --- 计算属性 (Computed Properties) ---

const t = computed(() => TRANSLATIONS[props.lang]);

const { scroller, onScroll } = useKeepScroll();

// 余额带千位分隔 (¥10,000.00)；按位数缩小字号，长金额不再溢出会员卡
const balance = computed(() => props.userProfile.balance || 0);
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
const setLang = (value: Language) => {
  if (value !== props.lang) emit('toggle-lang');
};

/**
 * 管理后台链接 (Admin URL)
 * 动态获取当前主机名，并使用 HTTPS 和 8080 端口。
 */
const adminUrl = computed(() => {
  const hostname = window.location.hostname;
  return `https://${hostname}:8080`;
});

/**
 * 同步资料到编辑表单
 */
watch(() => props.userProfile, (newVal) => {
  editForm.value = { ...newVal };
}, { immediate: true });

// --- 方法定义 (Methods) ---

/**
 * 保存资料修改
 */
const handleSaveProfile = () => {
    if (editForm.value.phone && !/^\d{11}$/.test(editForm.value.phone)) {
       toast.warning(props.lang === 'cn' ? "电话号码必须是11位数字" : "Phone number must be exactly 11 digits");
       return;
    }
    if (editForm.value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editForm.value.email)) {
       toast.warning(props.lang === 'cn' ? "邮箱格式无效" : "Invalid email format");
       return;
    }

  emit('update-profile', editForm.value);
  isEditing.value = false;
};

/**
 * 处理退出登录
 */
const handleLogout = () => {
    auth.clearToken();
    window.location.reload();
};

</script>

<template>
  <div class="relative h-full overflow-hidden">
    <Transition name="push" mode="out-in">
    <!-- SUB-VIEW: Order History -->
    <OrderHistoryList
      v-if="showHistory"
      :orders="orders"
      :lang="lang"
      @close="showHistory = false"
    />

    <!-- MAIN VIEW: Profile & Settings -->
    <div v-else class="flex flex-col h-full bg-background-light relative">
       <main ref="scroller" @scroll.passive="onScroll" class="flex-1 overflow-y-auto no-scrollbar px-5 md:px-10 pt-6 md:pt-10 pb-32">
         <div class="max-w-2xl mx-auto">

         <h1 class="font-serif text-[30px] md:text-[42px] font-normal leading-tight tracking-[-0.015em] text-text-main animate-fade-in">{{ t.profile }}</h1>

         <!-- Member card -->
         <div class="mt-6 rounded-card bg-primary text-white p-6 md:p-8 animate-slide-up-content" style="animation-delay: 60ms">
            <div class="flex items-start justify-between gap-4">
                <div class="min-w-0">
                    <p class="eyebrow !text-white/60">{{ t.memberLevel }}</p>
                    <h2 class="mt-2 font-serif text-[26px] md:text-[30px] font-normal leading-tight truncate">{{ userProfile.name || 'User' }}</h2>
                </div>
                <button
                   type="button"
                   @click="isEditing = true"
                   class="btn h-11 px-5 border border-white/30 text-white hover:bg-white/10 active:bg-white/10 shrink-0"
                >
                   {{ lang === 'cn' ? '编辑' : 'Edit' }}
                </button>
            </div>

            <div class="mt-10 flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
                <div class="min-w-0">
                    <p class="eyebrow !text-white/60">{{ t.balance }}</p>
                    <AnimatedNumber class="mt-2 block font-serif font-normal leading-none break-all" :class="balanceSize" :value="balance" :format="formatBalance" />
                </div>
                <p class="ml-auto text-[11px] tabular-nums tracking-wide text-white/55 text-right break-all max-w-[190px] leading-relaxed">{{ userProfile.uuid }}</p>
            </div>
         </div>

         <!-- Settings -->
         <div class="mt-10 border-y border-line divide-y divide-line">
             <button type="button" @click.stop="showHistory = true" class="group press-row w-[calc(100%+24px)] -mx-3 px-3 rounded-tile min-h-[72px] py-4 flex items-center gap-4 text-left">
                <span class="flex-1 min-w-0">
                   <span class="block text-[16px] text-text-main">{{ t.orderHistory }}</span>
                   <span class="block mt-0.5 text-[13px] text-text-sub">{{ t.viewDetailedHistory }}</span>
                </span>
                <AppIcon name="caret-right" weight="light" class="text-lg text-text-sub nudge" />
             </button>

             <div class="w-full min-h-[72px] py-3 flex items-center gap-4">
                <span class="flex-1 min-w-0 text-[16px] text-text-main">{{ t.language }}</span>
                <SlidingTabs :model-value="lang" @update:model-value="setLang" :options="langOptions" variant="segment" size="lg" stretch :label="t.language" class="w-[172px]" />
             </div>

             <button v-if="!demoMode" type="button" @click="showPasswordModal = true" class="group press-row w-[calc(100%+24px)] -mx-3 px-3 rounded-tile min-h-[72px] py-4 flex items-center gap-4 text-left">
                <span class="flex-1 min-w-0">
                   <span class="block text-[16px] text-text-main">{{ lang === 'cn' ? '修改密码' : 'Change Password' }}</span>
                   <span class="block mt-0.5 text-[13px] text-text-sub">{{ lang === 'cn' ? '更新您的账户密码' : 'Update your account password' }}</span>
                </span>
                <AppIcon name="caret-right" weight="light" class="text-lg text-text-sub nudge" />
             </button>

             <a v-if="!demoMode" :href="adminUrl" target="_blank" class="group press-row w-[calc(100%+24px)] -mx-3 px-3 rounded-tile min-h-[72px] py-4 flex items-center gap-4">
                <span class="flex-1 min-w-0">
                   <span class="block text-[16px] text-text-main">{{ lang === 'cn' ? '管理后台' : 'Admin System' }}</span>
                   <span class="block mt-0.5 text-[13px] text-text-sub">{{ lang === 'cn' ? '进入系统管理界面' : 'Access system administration' }}</span>
                </span>
                <AppIcon name="arrow-up-right" weight="light" class="text-lg text-text-sub nudge nudge-diag" />
             </a>
         </div>

         <button v-if="!demoMode" type="button" @click="handleLogout" class="mt-8 btn btn-danger-ghost w-full">
            {{ t.signOut }}
         </button>

         <p class="mt-6 text-center text-[12px] text-text-sub">OTIA Café · v3.0</p>
         </div>
       </main>
    </div>
    </Transition>

    <!-- Edit Profile Sheet -->
    <BottomSheet :open="isEditing" :title="lang === 'cn' ? '修改信息' : 'Edit Profile'" @close="isEditing = false">
       <div class="space-y-5">
          <label class="block">
             <span class="label">{{ lang === 'cn' ? '昵称' : 'Nickname' }}</span>
             <input class="field" v-model="editForm.name" autocomplete="nickname" enterkeyhint="next" />
          </label>
          <label class="block">
             <span class="label">{{ lang === 'cn' ? '手机号' : 'Phone' }}</span>
             <input class="field tabular-nums" v-model="editForm.phone" type="tel" inputmode="numeric" autocomplete="tel" maxlength="11" enterkeyhint="next" />
          </label>
          <label class="block">
             <span class="label">Email</span>
             <input class="field" v-model="editForm.email" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" enterkeyhint="done" />
          </label>
          <button type="button" @click="handleSaveProfile" class="btn btn-primary btn-lg w-full !mt-7">
               {{ lang === 'cn' ? '保存' : 'Save Changes' }}
          </button>
       </div>
    </BottomSheet>

    <!-- Password Sheet -->
    <PasswordModal
       :open="showPasswordModal"
       :lang="lang"
       @close="showPasswordModal = false"
    />
  </div>
</template>
