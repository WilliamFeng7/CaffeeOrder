<script setup lang="ts">
/**
 * SettingsView.vue
 * 
 * 设置与个人中心视图组件 (Settings & Profile View).
 */

import AppIcon from '@shared/components/AppIcon.vue';
import { ref, computed, watch } from 'vue';
import { TRANSLATIONS } from '../data';
import type { Order, Language, UserProfile } from '../types';
import { useToastStore } from '../stores/toast';

// 导入提取的子组件
import OrderHistoryList from '../components/OrderHistoryList.vue';
import { useSheetDrag } from '../composables/useSheetDrag';
import { useKeepScroll } from '../composables/useKeepScroll';
import PasswordModal from '../components/PasswordModal.vue';
import { auth } from '@shared/auth';

// --- Props & Emits 定义 ---

const props = defineProps<{
  userProfile: UserProfile; // 用户资料对象
  lang: Language;           // 当前语言
  orders: Order[];          // 订单列表数据
}>();

const emit = defineEmits<{
  (e: 'update-profile', profile: UserProfile): void; // 更新资料事件
  (e: 'toggle-lang'): void;                          // 切换语言事件
  (e: 'sign-out'): void;                             // 退出登录事件
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

// 编辑资料面板：按住顶部往下拖关闭
const editSheetEl = ref<HTMLElement | null>(null);
const editBackdropEl = ref<HTMLElement | null>(null);
const { handlers: editDragHandlers } = useSheetDrag({
  sheet: editSheetEl,
  backdrop: editBackdropEl,
  onDismiss: () => { isEditing.value = false; },
});

// 余额按位数缩小字号，长金额不再溢出会员卡
const balanceText = computed(() => `¥${(props.userProfile.balance || 0).toFixed(2)}`);
const balanceSize = computed(() => {
  const len = balanceText.value.length;
  if (len <= 9) return 'text-[40px] md:text-[48px]';
  if (len <= 12) return 'text-[32px] md:text-[40px]';
  return 'text-[26px] md:text-[32px]';
});

/**
 * 用户首字母缩写 (Initials)
 * 用于头像展示。
 */
const initials = computed(() => {
  const name = props.userProfile.name || props.userProfile.username || 'ME';
  return name.slice(0, 2).toUpperCase();
});

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

       <h1 class="font-serif text-[30px] md:text-[40px] font-medium leading-tight tracking-[-0.01em] text-text-main">{{ t.profile }}</h1>

       <!-- Member card -->
       <div
          class="mt-6 rounded-card bg-primary text-white p-6 md:p-8 cursor-pointer transition-transform duration-release ease-out active:duration-press active:scale-[0.99]"
          @click="isEditing = true"
       >
          <div class="flex items-start justify-between gap-3">
              <div class="flex items-center gap-4 min-w-0">
                  <div class="size-14 rounded-full bg-white/15 flex items-center justify-center text-lg font-medium shrink-0">
                      {{ initials }}
                  </div>
                  <div class="min-w-0">
                      <h2 class="font-serif text-[24px] md:text-[28px] font-medium leading-tight truncate">{{ userProfile.name || 'User' }}</h2>
                      <p class="mt-1 flex items-center gap-1 text-[13px] text-white/75">
                          <AppIcon name="star" weight="fill" class="text-secondary text-xs" />
                          {{ t.memberLevel }}
                      </p>
                  </div>
              </div>
              <button type="button" :aria-label="lang === 'cn' ? '修改信息' : 'Edit Profile'" class="size-10 rounded-full border border-white/25 flex items-center justify-center shrink-0">
                  <AppIcon name="edit" class="text-base" />
              </button>
          </div>

          <div class="mt-8 flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
              <div class="min-w-0">
                  <p class="text-[12px] font-medium tracking-[0.14em] uppercase text-white/70">{{ t.balance }}</p>
                  <p class="mt-1 font-serif font-medium tabular-nums break-all leading-none" :class="balanceSize">{{ balanceText }}</p>
              </div>
              <p class="ml-auto text-[11px] font-mono text-white/55 text-right break-all max-w-[190px] leading-relaxed">{{ userProfile.uuid }}</p>
          </div>
       </div>

       <!-- Settings -->
       <div class="mt-8 border-y border-line divide-y divide-line">
           <button type="button" @click.stop="showHistory = true" class="w-full min-h-[64px] py-3 flex items-center gap-4 text-left active:opacity-60">
              <AppIcon name="history" class="text-[22px] text-text-main" />
              <span class="flex-1 min-w-0">
                 <span class="block text-[16px] text-text-main">{{ t.orderHistory }}</span>
                 <span class="block text-[13px] text-text-sub">{{ t.viewDetailedHistory }}</span>
              </span>
              <AppIcon name="caret-right" class="text-base text-text-sub" />
           </button>

           <button type="button" @click="emit('toggle-lang')" class="w-full min-h-[64px] py-3 flex items-center gap-4 text-left active:opacity-60">
              <AppIcon name="translate" class="text-[22px] text-text-main" />
              <span class="flex-1 min-w-0 text-[16px] text-text-main">{{ t.language }}</span>
              <span class="text-[15px] text-text-sub">{{ lang === 'cn' ? '中文' : 'English' }}</span>
              <AppIcon name="swap" class="text-base text-text-sub" />
           </button>

           <button type="button" @click="showPasswordModal = true" class="w-full min-h-[64px] py-3 flex items-center gap-4 text-left active:opacity-60">
              <AppIcon name="key" class="text-[22px] text-text-main" />
              <span class="flex-1 min-w-0">
                 <span class="block text-[16px] text-text-main">{{ lang === 'cn' ? '修改密码' : 'Change Password' }}</span>
                 <span class="block text-[13px] text-text-sub">{{ lang === 'cn' ? '更新您的账户密码' : 'Update your account password' }}</span>
              </span>
              <AppIcon name="caret-right" class="text-base text-text-sub" />
           </button>

           <a :href="adminUrl" target="_blank" class="w-full min-h-[64px] py-3 flex items-center gap-4 active:opacity-60">
              <AppIcon name="shield" class="text-[22px] text-text-main" />
              <span class="flex-1 min-w-0">
                 <span class="block text-[16px] text-text-main">{{ lang === 'cn' ? '管理后台' : 'Admin System' }}</span>
                 <span class="block text-[13px] text-text-sub">{{ lang === 'cn' ? '进入系统管理界面' : 'Access system administration' }}</span>
              </span>
              <AppIcon name="external" class="text-base text-text-sub" />
           </a>
       </div>

       <button type="button" @click="handleLogout" class="mt-8 w-full h-12 rounded-full border border-line text-[15px] font-medium text-[#B42318] active:bg-cream">
          {{ t.signOut }}
       </button>

       <p class="mt-6 text-center text-[12px] text-text-sub">OTIA Café · v3.0</p>
       </div>
     </main>

     <!-- Edit Profile Sheet -->
     <div v-if="isEditing" class="fixed inset-0 z-50 flex items-end md:items-center justify-center pointer-events-none">
        <div ref="editBackdropEl" class="absolute inset-0 bg-black/35 pointer-events-auto animate-fade-in" @click="isEditing = false"></div>
        <div ref="editSheetEl" role="dialog" aria-modal="true" class="bg-surface-light w-full md:w-[460px] rounded-t-sheet md:rounded-sheet px-6 pt-2 relative z-10 pointer-events-auto shadow-sheet animate-slide-up-modal md:animate-scale-in pb-[max(env(safe-area-inset-bottom),32px)] md:pb-8">
           <!-- Drag handle: swipe down to close -->
           <div class="touch-none -mx-6 px-6 pt-2 pb-6" v-on="editDragHandlers">
              <div class="w-9 h-1 bg-line rounded-full mx-auto mb-5" aria-hidden="true"></div>
              <h3 class="font-serif text-[24px] font-medium text-text-main">{{ lang === 'cn' ? '修改信息' : 'Edit Profile' }}</h3>
           </div>
           <div class="space-y-5">
              <label class="block">
                 <span class="block text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub mb-2">{{ lang === 'cn' ? '昵称' : 'Nickname' }}</span>
                 <input class="w-full h-12 px-4 rounded-tile bg-cream border border-transparent text-[16px] text-text-main outline-none transition-[background-color,border-color] duration-color focus:bg-surface-light focus:border-line" v-model="editForm.name" autocomplete="nickname" enterkeyhint="next" />
              </label>
              <label class="block">
                 <span class="block text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub mb-2">{{ lang === 'cn' ? '手机号' : 'Phone' }}</span>
                 <input class="w-full h-12 px-4 rounded-tile bg-cream border border-transparent text-[16px] text-text-main outline-none transition-[background-color,border-color] duration-color focus:bg-surface-light focus:border-line tabular-nums" v-model="editForm.phone" type="tel" inputmode="numeric" autocomplete="tel" maxlength="11" enterkeyhint="next" />
              </label>
              <label class="block">
                 <span class="block text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub mb-2">Email</span>
                 <input class="w-full h-12 px-4 rounded-tile bg-cream border border-transparent text-[16px] text-text-main outline-none transition-[background-color,border-color] duration-color focus:bg-surface-light focus:border-line" v-model="editForm.email" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" enterkeyhint="done" />
              </label>
              <button type="button" @click="handleSaveProfile" class="w-full h-14 mt-2 rounded-full bg-primary text-white text-[16px] font-medium active:bg-primary-dark">
                   {{ lang === 'cn' ? '保存' : 'Save Changes' }}
              </button>
           </div>
        </div>
     </div>

     <!-- Password Modal -->
     <PasswordModal
        v-if="showPasswordModal"
        :lang="lang"
        @close="showPasswordModal = false"
     />
  </div>
</template>
