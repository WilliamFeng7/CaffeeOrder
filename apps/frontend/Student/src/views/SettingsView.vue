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
  if (len <= 9) return 'text-4xl md:text-5xl';
  if (len <= 12) return 'text-3xl md:text-4xl';
  return 'text-2xl md:text-3xl';
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
     <main ref="scroller" @scroll.passive="onScroll" class="flex-1 overflow-y-auto no-scrollbar px-4 md:px-8 pt-6 md:pt-8 pb-32">
       <div class="max-w-2xl mx-auto space-y-5">

       <h1 class="font-display text-[26px] md:text-3xl font-bold tracking-tight text-text-main">{{ t.profile }}</h1>

       <!-- Member Card -->
       <div
          class="relative rounded-card overflow-hidden bg-primary text-white p-5 md:p-7 shadow-card cursor-pointer transition-transform duration-200 ease-out active:scale-[0.99] bg-[radial-gradient(120%_120%_at_100%_0%,rgba(255,255,255,0.16),transparent_55%)]"
          @click="isEditing = true"
       >
          <AppIcon name="coffee" class="absolute -right-6 -bottom-8 text-[160px] text-white/[0.06] pointer-events-none" />

          <div class="relative flex items-start justify-between gap-3">
              <div class="flex items-center gap-3.5 min-w-0">
                  <div class="size-14 md:size-16 rounded-full bg-white/15 flex items-center justify-center text-xl md:text-2xl font-bold shrink-0">
                      {{ initials }}
                  </div>
                  <div class="min-w-0">
                      <h2 class="font-display text-xl md:text-2xl font-bold tracking-tight truncate">{{ userProfile.name || 'User' }}</h2>
                      <span class="mt-1.5 inline-flex h-6 px-2.5 items-center gap-1 rounded-full bg-secondary-soft text-secondary-content text-[12px] font-semibold">
                          <AppIcon name="star" weight="fill" class="text-secondary text-xs" />
                          {{ t.memberLevel }}
                      </span>
                  </div>
              </div>
              <button type="button" :aria-label="lang === 'cn' ? '修改信息' : 'Edit Profile'" class="size-10 rounded-full bg-white/15 flex items-center justify-center active:bg-white/25 shrink-0">
                  <AppIcon name="edit" class="text-lg" />
              </button>
          </div>

          <div class="relative mt-6 flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
              <div class="min-w-0">
                  <p class="text-[13px] text-white/70">{{ t.balance }}</p>
                  <p class="mt-1 font-display font-bold tracking-tight tabular-nums break-all leading-none" :class="balanceSize">{{ balanceText }}</p>
              </div>
              <p class="ml-auto text-[11px] font-mono text-white/55 text-right break-all max-w-[190px] leading-relaxed">{{ userProfile.uuid }}</p>
          </div>
       </div>

       <!-- Settings list -->
       <div class="bg-white rounded-card shadow-card overflow-hidden divide-y divide-line">
           <button type="button" @click.stop="showHistory = true" class="w-full min-h-[68px] px-4 py-3 flex items-center gap-3.5 text-left active:bg-cream/50">
              <span class="size-10 rounded-[12px] bg-primary-soft text-primary flex items-center justify-center shrink-0"><AppIcon name="history" class="text-xl" /></span>
              <span class="flex-1 min-w-0">
                 <span class="block text-[16px] font-semibold text-text-main">{{ t.orderHistory }}</span>
                 <span class="block text-[13px] text-text-sub">{{ t.viewDetailedHistory }}</span>
              </span>
              <AppIcon name="caret-right" class="text-text-sub text-base" />
           </button>

           <button type="button" @click="emit('toggle-lang')" class="w-full min-h-[68px] px-4 py-3 flex items-center gap-3.5 text-left active:bg-cream/50">
              <span class="size-10 rounded-[12px] bg-primary-soft text-primary flex items-center justify-center shrink-0"><AppIcon name="translate" class="text-xl" /></span>
              <span class="flex-1 min-w-0 text-[16px] font-semibold text-text-main">{{ t.language }}</span>
              <span class="text-[15px] text-text-sub">{{ lang === 'cn' ? '中文' : 'English' }}</span>
              <AppIcon name="swap" class="text-text-sub text-base" />
           </button>

           <button type="button" @click="showPasswordModal = true" class="w-full min-h-[68px] px-4 py-3 flex items-center gap-3.5 text-left active:bg-cream/50">
              <span class="size-10 rounded-[12px] bg-primary-soft text-primary flex items-center justify-center shrink-0"><AppIcon name="key" class="text-xl" /></span>
              <span class="flex-1 min-w-0">
                 <span class="block text-[16px] font-semibold text-text-main">{{ lang === 'cn' ? '修改密码' : 'Change Password' }}</span>
                 <span class="block text-[13px] text-text-sub">{{ lang === 'cn' ? '更新您的账户密码' : 'Update your account password' }}</span>
              </span>
              <AppIcon name="caret-right" class="text-text-sub text-base" />
           </button>

           <a :href="adminUrl" target="_blank" class="w-full min-h-[68px] px-4 py-3 flex items-center gap-3.5 active:bg-cream/50">
              <span class="size-10 rounded-[12px] bg-cream text-text-main flex items-center justify-center shrink-0"><AppIcon name="shield" class="text-xl" /></span>
              <span class="flex-1 min-w-0">
                 <span class="block text-[16px] font-semibold text-text-main">{{ lang === 'cn' ? '管理后台' : 'Admin System' }}</span>
                 <span class="block text-[13px] text-text-sub">{{ lang === 'cn' ? '进入系统管理界面' : 'Access system administration' }}</span>
              </span>
              <AppIcon name="external" class="text-text-sub text-base" />
           </a>
       </div>

       <button type="button" @click="handleLogout" class="w-full min-h-[56px] bg-white rounded-card shadow-card text-[16px] font-semibold text-[#B42318] active:bg-cream/50">
          {{ t.signOut }}
       </button>

       <p class="text-center text-[12px] text-text-sub/70">OTIA Café · v3.0</p>
       </div>
     </main>

     <!-- Edit Profile Sheet -->
     <div v-if="isEditing" class="fixed inset-0 z-50 flex items-end md:items-center justify-center pointer-events-none">
        <div ref="editBackdropEl" class="absolute inset-0 bg-black/40 pointer-events-auto animate-fade-in" @click="isEditing = false"></div>
        <div ref="editSheetEl" role="dialog" aria-modal="true" class="bg-white w-full md:w-[460px] rounded-t-sheet md:rounded-sheet px-6 pt-2 relative z-10 pointer-events-auto shadow-sheet animate-slide-up-modal md:animate-scale-in pb-[max(env(safe-area-inset-bottom),32px)] md:pb-8">
           <!-- Drag handle: swipe down to close -->
           <div class="touch-none -mx-6 px-6 pt-2 pb-6" v-on="editDragHandlers">
              <div class="w-10 h-1.5 bg-line rounded-full mx-auto mb-5" aria-hidden="true"></div>
              <h3 class="font-display text-xl font-bold text-text-main">{{ lang === 'cn' ? '修改信息' : 'Edit Profile' }}</h3>
           </div>
           <div class="space-y-4">
              <label class="block space-y-1.5">
                 <span class="block text-[13px] font-semibold text-text-sub">{{ lang === 'cn' ? '昵称' : 'Nickname' }}</span>
                 <input class="w-full h-12 px-4 rounded-tile bg-background-light border border-line text-[16px] font-medium text-text-main outline-none transition-[border-color,box-shadow] duration-150 focus:border-primary/40 focus:ring-4 focus:ring-primary/10" v-model="editForm.name" autocomplete="nickname" enterkeyhint="next" />
              </label>
              <label class="block space-y-1.5">
                 <span class="block text-[13px] font-semibold text-text-sub">{{ lang === 'cn' ? '手机号' : 'Phone' }}</span>
                 <input class="w-full h-12 px-4 rounded-tile bg-background-light border border-line text-[16px] font-medium text-text-main outline-none transition-[border-color,box-shadow] duration-150 focus:border-primary/40 focus:ring-4 focus:ring-primary/10 tabular-nums" v-model="editForm.phone" type="tel" inputmode="numeric" autocomplete="tel" maxlength="11" enterkeyhint="next" />
              </label>
              <label class="block space-y-1.5">
                 <span class="block text-[13px] font-semibold text-text-sub">Email</span>
                 <input class="w-full h-12 px-4 rounded-tile bg-background-light border border-line text-[16px] font-medium text-text-main outline-none transition-[border-color,box-shadow] duration-150 focus:border-primary/40 focus:ring-4 focus:ring-primary/10" v-model="editForm.email" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" enterkeyhint="done" />
              </label>
              <button type="button" @click="handleSaveProfile" class="w-full h-14 mt-2 rounded-full bg-primary text-white font-semibold text-[17px] active:bg-primary-dark">
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
