<script setup lang="ts">
/**
 * SettingsView.vue
 * 
 * 设置与个人中心视图组件 (Settings & Profile View).
 */

import { ref, computed, watch } from 'vue';
import { TRANSLATIONS } from '../data';
import type { Order, Language, UserProfile } from '../types';
import { useToastStore } from '../stores/toast';

// 导入提取的子组件
import OrderHistoryList from '../components/OrderHistoryList.vue';
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

/**
 * 用户首字母缩写 (Initials)
 * 用于头像展示。
 */
const initials = computed(() => {
  const name = props.userProfile.name || props.userProfile.username || 'ME';
  return name.slice(0, 2).toUpperCase();
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
  <div v-else class="flex flex-col h-full bg-background-light animate-fade-in relative">
     <main class="flex-1 overflow-y-auto p-6 pt-20 space-y-8 pb-32">
       
       <!-- Page Title -->
       <div class="px-2 mb-6">
           <h1 class="text-4xl font-sans font-black text-[#103E32] tracking-tighter">{{ t.profile }}</h1>
       </div>

       <!-- Member Card -->
       <div 
          class="w-full relative group active:scale-[0.98] transition-all duration-500 ease-luxury" 
          @click="isEditing = true"
       >
          <div class="bg-gradient-to-br from-[#103E32] to-[#051F19] rounded-[32px] p-8 md:p-10 relative overflow-hidden shadow-2xl shadow-[#103E32]/30 text-white min-h-[240px] flex flex-col justify-between border border-white/5">
              <div class="absolute -top-20 -right-20 size-64 bg-[#DCCA98]/10 rounded-full blur-3xl opacity-50"></div>
              <div class="absolute bottom-0 left-0 size-48 bg-[#DCCA98]/5 rounded-full blur-3xl"></div>

              <div class="relative z-10 flex justify-between items-start">
                  <div class="flex items-center gap-5">
                      <div class="size-20 rounded-full border-2 border-[#DCCA98]/30 p-1.5 backdrop-blur-sm bg-white/5">
                            <div class="w-full h-full rounded-full bg-[#DCCA98] text-[#103E32] flex items-center justify-center font-sans font-black text-3xl shadow-inner">
                                {{ initials }}
                            </div>
                      </div>
                      <div>
                          <h2 class="font-sans font-black text-3xl text-white tracking-tight">{{ userProfile.name || 'User' }}</h2>
                          <div class="mt-2 inline-flex items-center px-3 py-1 bg-[#DCCA98] rounded-full shadow-lg shadow-[#DCCA98]/20">
                              <span class="text-[#103E32] text-[10px] font-black uppercase tracking-[0.15em]">Gold Member</span>
                          </div>
                      </div>
                  </div>
                  <button class="size-12 rounded-full bg-white/10 backdrop-blur-md border border-white/10 flex items-center justify-center active:bg-white/20 transition-colors">
                      <span class="material-symbols-rounded text-xl">edit</span>
                  </button>
              </div>

              <div class="relative z-10 pl-2">
                 <p class="text-xs text-white/50 font-medium tracking-wide font-mono mt-1" v-if="userProfile.email">{{ userProfile.email }}</p>
              </div>

              <div class="relative z-10 mt-8 flex items-end justify-between border-t border-white/10 pt-6">
                  <div>
                      <p class="text-[#DCCA98] text-[10px] font-black uppercase tracking-[0.2em] opacity-80 mb-2">{{ t.balance }}</p>
                      <span class="font-sans text-6xl font-black tracking-tighter text-white drop-shadow-lg">¥{{ (userProfile.balance || 0).toFixed(2) }}</span>
                  </div>
                  <div class="flex flex-col items-end">
                    <p class="text-[#DCCA98] text-[10px] font-black uppercase tracking-[0.2em] opacity-80 mb-2">USER ID</p>
                    <p class="text-xs font-mono text-white/90 break-all max-w-[180px] text-right font-bold tracking-wider leading-relaxed opacity-60">
                        {{ userProfile.uuid }}
                    </p>
                  </div>
              </div>
          </div>
       </div>

       <!-- Menu Items -->
       <div class="space-y-5">
           <button @click.stop="showHistory = true" class="w-full bg-white p-7 rounded-[32px] flex items-center justify-between shadow-[0_8px_30px_rgba(0,0,0,0.04)] active:scale-[0.98] transition-all duration-500 ease-luxury border border-gray-50">
              <div class="flex items-center gap-5">
                 <div class="size-14 rounded-2xl bg-[#F2F7F5] flex items-center justify-center text-[#103E32]"><span class="material-symbols-rounded text-2xl">history</span></div>
                 <div class="text-left">
                    <p class="font-sans font-bold text-xl text-text-main tracking-tight">{{ t.orderHistory }}</p>
                    <p class="text-xs text-gray-400 mt-1 font-medium tracking-wide">{{ t.viewDetailedHistory }}</p>
                 </div>
              </div>
              <span class="material-symbols-rounded text-gray-300">chevron_right</span>
           </button>

           <button @click="emit('toggle-lang')" class="w-full bg-white p-7 rounded-[32px] flex items-center justify-between shadow-[0_8px_30px_rgba(0,0,0,0.04)] active:scale-[0.98] transition-all duration-500 ease-luxury border border-gray-50">
              <div class="flex items-center gap-5">
                 <div class="size-14 rounded-2xl bg-[#F2F7F5] flex items-center justify-center text-[#103E32]"><span class="material-symbols-rounded text-2xl">language</span></div>
                 <div class="text-left">
                    <p class="font-sans font-bold text-xl text-text-main tracking-tight">{{ t.language }}</p>
                    <div class="flex gap-2 mt-1.5">
                       <span class="text-[10px] font-black px-3 py-1 rounded-full transition-colors" :class="lang === 'en' ? 'bg-[#103E32] text-white' : 'bg-gray-100 text-gray-400'">EN</span>
                       <span class="text-[10px] font-black px-3 py-1 rounded-full transition-colors" :class="lang === 'cn' ? 'bg-[#103E32] text-white' : 'bg-gray-100 text-gray-400'">CN</span>
                    </div>
                 </div>
              </div>
              <span class="material-symbols-rounded text-gray-300">swap_horiz</span>
           </button>

           <button @click="showPasswordModal = true" class="w-full bg-white p-7 rounded-[32px] flex items-center justify-between shadow-[0_8px_30px_rgba(0,0,0,0.04)] active:scale-[0.98] transition-all duration-500 ease-luxury border border-gray-50">
              <div class="flex items-center gap-5">
                 <div class="size-14 rounded-2xl bg-[#F2F7F5] flex items-center justify-center text-[#103E32]"><span class="material-symbols-rounded text-2xl">lock_reset</span></div>
                 <div class="text-left">
                    <p class="font-sans font-bold text-xl text-text-main tracking-tight">{{ lang === 'cn' ? '修改密码' : 'Change Password' }}</p>
                    <p class="text-xs text-gray-400 mt-1 font-medium tracking-wide">{{ lang === 'cn' ? '更新您的账户密码' : 'Update your account password' }}</p>
                 </div>
              </div>
              <span class="material-symbols-rounded text-gray-300">chevron_right</span>
           </button>

           <a href="http://localhost:8080" target="_blank" class="w-full bg-gradient-to-r from-gray-900 to-gray-800 p-7 rounded-[32px] flex items-center justify-between shadow-lg shadow-gray-900/20 active:scale-[0.98] transition-all duration-500 ease-luxury border border-gray-700 block">
              <div class="flex items-center gap-5">
                 <div class="size-14 rounded-2xl bg-white/10 flex items-center justify-center text-white backdrop-blur-sm"><span class="material-symbols-rounded text-2xl">admin_panel_settings</span></div>
                 <div class="text-left">
                    <p class="font-sans font-bold text-xl text-white tracking-tight">{{ lang === 'cn' ? '管理后台' : 'Admin System' }}</p>
                    <p class="text-xs text-white/50 mt-1 font-medium tracking-wide">{{ lang === 'cn' ? '进入系统管理界面' : 'Access system administration' }}</p>
                 </div>
              </div>
              <span class="material-symbols-rounded text-white/50">open_in_new</span>
           </a>
           
           <button @click="handleLogout" class="w-full p-5 mt-6 text-center active:opacity-60 transition-opacity">
              <span class="text-xs font-black uppercase tracking-[0.2em] text-[#103E32]/50 active:text-red-500 transition-colors">{{ t.signOut }}</span>
           </button>
       </div>
       
       <div class="text-center pt-4 opacity-20"><p class="text-[9px] font-black uppercase tracking-widest">Coffee App v3.0</p></div>
     </main>

     <!-- Edit Profile Modal -->
     <div v-if="isEditing" class="fixed inset-0 z-50 flex items-end md:items-center justify-center pointer-events-none">
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm pointer-events-auto transition-opacity" @click="isEditing = false"></div>
        <div class="bg-white w-full md:w-[480px] rounded-t-[32px] md:rounded-[32px] p-8 relative z-10 pointer-events-auto animate-slide-up-modal pb-10">
           <div class="w-12 h-1 bg-gray-200 rounded-full mx-auto mb-8"></div>
           <h3 class="text-2xl font-black text-text-main mb-8">{{ lang === 'cn' ? '修改信息' : 'Edit Profile' }}</h3>
           <div class="space-y-6">
              <div class="space-y-2">
                 <label class="text-[10px] font-black text-gray-400 uppercase tracking-wider ml-4">{{ lang === 'cn' ? '昵称' : 'Nickname' }}</label>
                 <input class="w-full h-14 px-6 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-primary/20 font-bold text-lg" v-model="editForm.name" />
              </div>
              <div class="space-y-2">
                 <label class="text-[10px] font-black text-gray-400 uppercase tracking-wider ml-4">{{ lang === 'cn' ? '手机号' : 'Phone' }}</label>
                 <input class="w-full h-14 px-6 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-primary/20 font-bold text-lg" v-model="editForm.phone" />
              </div>
              <div class="space-y-2">
                 <label class="text-[10px] font-black text-gray-400 uppercase tracking-wider ml-4">Email</label>
                 <input class="w-full h-14 px-6 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-primary/20 font-bold text-lg" v-model="editForm.email" />
              </div>
              <button @click="handleSaveProfile" class="w-full h-16 rounded-[24px] font-black text-white bg-[#103E32] shadow-xl shadow-[#103E32]/20 active:scale-[0.96] transition-all duration-500 ease-luxury mt-6 text-lg tracking-wide">
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
