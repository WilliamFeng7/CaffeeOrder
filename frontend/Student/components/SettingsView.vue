<script setup lang="ts">
/**
 * SettingsView.vue
 * 
 * 设置与个人中心视图组件 (Settings & Profile View).
 * 
 * 主要功能 (Core Features):
 * 1. 个人资料展示 (Profile): 显示头像、姓名、会员等级、余额等。
 * 2. 资料编辑 (Edit Profile): 修改姓名、电话、邮箱。
 * 3. 密码修改 (Change Password): 提供安全的密码更新功能。
 * 4. 订单历史 (Order History): 独立的全屏历史记录视图，支持查看订单详情和状态。
 * 5. 系统设置 (Settings): 语言切换、退出登录。
 */

import { ref, computed, watch } from 'vue';
import { TRANSLATIONS } from '../data';
import type { Order, Language, UserProfile } from '../types';
import { api } from '../api';
import { useToastStore } from '../src/stores/toast';

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

// 是否显示历史记录子视图
const showHistory = ref(false);
const toast = useToastStore();

// 是否显示编辑资料弹窗
const isEditing = ref(false);

// 编辑表单数据绑定
const editForm = ref<UserProfile>({
    name: '',
    phone: '',
    email: '',
    avatar: '',
    uuid: ''
});

// --- 密码修改相关状态 ---
const showPasswordModal = ref(false);
const passwordForm = ref({
   oldPassword: '',
   newPassword: '',
   confirmPassword: ''
});
const passwordError = ref('');

// --- 计算属性 (Computed Properties) ---

// 语言翻译包
const t = computed(() => TRANSLATIONS[props.lang]);

/**
 * 排序后的历史订单 (Sorted History)
 * 按日期降序排列 (最新的在最前)。
 * 注意: 创建副本以避免直接修改 props。
 */
const historyOrders = computed(() => {
    return [...props.orders].sort((a, b) => {
        return new Date(b.date).getTime() - new Date(a.date).getTime();
    });
});

/**
 * 用户首字母缩写 (Initials)
 * 用于头像展示。如果无名字则显示 "ME"。
 */
const initials = computed(() => {
  const name = props.userProfile.name || props.userProfile.username || 'ME';
  return name.slice(0, 2).toUpperCase();
});

/**
 * 监听 userProfile 变化并同步到编辑表单
 * ensure form is in sync when props load.
 */
watch(() => props.userProfile, (newVal) => {
  editForm.value = { ...newVal };
}, { immediate: true });

// --- 方法定义 (Methods) ---

/**
 * 保存资料修改
 * 包含基础的格式校验 (手机号、邮箱)。
 */
const handleSaveProfile = () => {
    // 1. 校验手机号 (11位数字)
    if (editForm.value.phone && !/^\d{11}$/.test(editForm.value.phone)) {
       const msg = props.lang === 'cn' ? "电话号码必须是11位数字" : "Phone number must be exactly 11 digits";
       toast.warning(msg);
       return;
    }
    // 2. 校验邮箱格式
    if (editForm.value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editForm.value.email)) {
       const msg = props.lang === 'cn' ? "邮箱格式无效" : "Invalid email format";
       toast.warning(msg);
       return;
    }

  emit('update-profile', editForm.value);
  isEditing.value = false;
};

/**
 * 格式化日期时间
 * Format: YYYY/MM/DD HH:mm:ss
 */
const formatDate = (dateStr: string) => {
  try {
      const d = new Date(dateStr);
      return d.toLocaleString('zh-CN', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
      });
  } catch (e) {
      return dateStr;
  }
};

/**
 * 处理密码修改
 * 调用 API 更新密码，成功后重置表单。
 */
const handlePasswordChange = async () => {
   // 1. 基础校验 (判空、长度、一致性)
   if (!passwordForm.value.oldPassword || !passwordForm.value.newPassword || !passwordForm.value.confirmPassword) {
      passwordError.value = props.lang === 'cn' ? '请填写所有字段' : 'Please fill in all fields';
      return;
   }
   if (passwordForm.value.newPassword.length < 8) {
      passwordError.value = props.lang === 'cn' ? '新密码至少8位' : 'New password must be at least 8 characters';
      return;
   }
   if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
      passwordError.value = props.lang === 'cn' ? '两次密码不一致' : 'Passwords do not match';
      return;
   }
   
   try {
      // 2. API 调用
      await api.updatePassword(passwordForm.value.oldPassword, passwordForm.value.newPassword);
      showPasswordModal.value = false;
      // 3. 重置表单
      passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' };
      toast.success(props.lang === 'cn' ? '密码修改成功' : 'Password updated successfully');
   } catch (e: any) {
      passwordError.value = e.message;
   }
};

/**
 * 处理退出登录
 * 清除 Token 并强制刷新页面。
 */
const handleLogout = () => {
    sessionStorage.removeItem('token');
    window.location.reload();
};

</script>

<template>
  <!-- SUB-VIEW: Order History (Detail View) -->
  <!-- 子视图：订单历史详情页 -->
  <div v-if="showHistory" class="flex flex-col h-full bg-background-light animate-slide-up-content">
     <!-- Header Navigation -->
     <header class="flex items-center p-6 pt-12 sticky top-0 bg-background-light/95 backdrop-blur z-20">
       <button 
           @click="showHistory = false" 
           class="flex items-center justify-center size-12 rounded-full bg-white shadow-sm active:scale-90 transition-all font-black"
       >
          <span class="material-symbols-rounded text-text-main">arrow_back</span>
       </button>
       <h1 class="text-2xl font-black ml-4 text-text-main">{{ t.orderHistory }}</h1>
     </header>
     
     <!-- History List -->
     <main class="flex-1 overflow-y-auto p-6 space-y-6 pb-32">
        <!-- Empty State -->
        <div v-if="orders.length === 0" class="h-64 flex flex-col items-center justify-center text-gray-400">
          <span class="material-symbols-rounded text-6xl opacity-20">history</span>
          <p class="mt-4 font-bold">{{ t.noOrders }}</p>
        </div>
        
        <!-- Order Card -->
        <div 
          v-else
          v-for="(order, idx) in historyOrders" 
          :key="order.id" 
          class="bg-white p-6 rounded-[24px] shadow-sm border border-gray-100" 
        >
            <!-- Order Header Info -->
            <div class="flex justify-between items-start mb-4 pb-4 border-b border-gray-50">
                <div class="space-y-1">
                  <!-- Date -->
                  <p class="text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                      {{ formatDate(order.date) }}
                  </p>
                  <!-- Pickup Number -->
                  <h3 class="text-xl font-black text-primary">#{{ order.dailyNumber }}</h3>
                  
                  <!-- UUIDs for verification -->
                  <div class="flex flex-col gap-0.5 mt-2">
                       <p class="text-[9px] text-gray-400 font-mono">
                           <span class="opacity-50">OID:</span> {{ order.order_no }}
                       </p>
                  </div>
                </div>
                
                <div class="text-right">
                  <!-- Total Price -->
                  <span class="block text-2xl font-black text-text-main">¥{{ order.total.toFixed(2) }}</span>
                  <!-- Status Tag -->
                  <div class="mt-2 flex justify-end">
                    <span 
                        class="px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-wider"
                        :class="order.isCompleted ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'"
                    >
                        {{ order.isCompleted ? t.completed : 'Pending' }}
                    </span>
                  </div>
                </div>
            </div>

            <!-- Order Items List -->
            <div class="space-y-3">
                <div v-for="(item, i) in order.items" :key="i" class="flex items-center gap-3">
                    <div 
                        class="size-12 rounded-xl bg-gray-50 bg-cover bg-center shrink-0" 
                        :style="{ backgroundImage: `url(${item.image})` }"
                    ></div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-black text-text-main truncate">
                            {{ lang === 'cn' ? (item.nameCN || item.name) : item.name }}
                        </p>
                        <p class="text-[10px] text-gray-400 truncate">
                            {{ item.temperature }} · {{ item.sugar }}
                        </p>
                    </div>
                    <span class="text-sm font-bold text-text-main">x{{ item.quantity }}</span>
                </div>
            </div>
        </div>
     </main>
  </div>

  <!-- MAIN VIEW: Profile & Settings -->
  <!-- 主界面：个人中心 -->
  <div v-else class="flex flex-col h-full bg-background-light animate-fade-in relative">
     <main class="flex-1 overflow-y-auto p-6 pt-20 space-y-8 pb-32">
       
       <!-- Page Title -->
       <div class="px-2 mb-6">
           <h1 class="text-4xl font-sans font-black text-[#103E32] tracking-tighter">{{ t.profile }}</h1>
       </div>

       <!-- Member Card (Click to Edit) -->
       <!-- 会员卡片 (点击编辑) -->
       <div 
          class="w-full relative group active:scale-[0.98] transition-all duration-500 ease-luxury" 
          @click="isEditing = true"
       >
          <div class="bg-gradient-to-br from-[#103E32] to-[#051F19] rounded-[32px] p-8 md:p-10 relative overflow-hidden shadow-2xl shadow-[#103E32]/30 text-white min-h-[240px] flex flex-col justify-between border border-white/5">
              <!-- Decorative Elements -->
              <div class="absolute -top-20 -right-20 size-64 bg-[#DCCA98]/10 rounded-full blur-3xl opacity-50"></div>
              <div class="absolute bottom-0 left-0 size-48 bg-[#DCCA98]/5 rounded-full blur-3xl"></div>

              <!-- Top Section: Avatar & Name -->
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
                  <!-- Edit Icon -->
                  <button class="size-12 rounded-full bg-white/10 backdrop-blur-md border border-white/10 flex items-center justify-center active:bg-white/20 transition-colors">
                      <span class="material-symbols-rounded text-xl">edit</span>
                  </button>
              </div>

              <!-- Middle Section: Email -->
              <div class="relative z-10 pl-2">
                 <p class="text-xs text-white/50 font-medium tracking-wide font-mono mt-1" v-if="userProfile.email">{{ userProfile.email }}</p>
              </div>

              <!-- Bottom Section: Balance & UUID -->
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

       <!-- Menu Items Buttons -->
       <!-- 菜单按钮列表 -->
       <div class="space-y-5">
           <!-- History Button -->
           <button 
              @click.stop="showHistory = true"
              class="w-full bg-white p-7 rounded-[32px] flex items-center justify-between shadow-[0_8px_30px_rgba(0,0,0,0.04)] active:scale-[0.98] transition-all duration-500 ease-luxury border border-gray-50"
           >
              <div class="flex items-center gap-5">
                 <div class="size-14 rounded-2xl bg-[#F2F7F5] flex items-center justify-center text-[#103E32]">
                    <span class="material-symbols-rounded text-2xl">history</span>
                 </div>
                 <div class="text-left">
                    <p class="font-sans font-bold text-xl text-text-main tracking-tight">{{ t.orderHistory }}</p>
                    <p class="text-xs text-gray-400 mt-1 font-medium tracking-wide">{{ t.viewDetailedHistory }}</p>
                 </div>
              </div>
              <span class="material-symbols-rounded text-gray-300">chevron_right</span>
           </button>

           <!-- Language Toggle -->
           <button 
              @click="emit('toggle-lang')"
              class="w-full bg-white p-7 rounded-[32px] flex items-center justify-between shadow-[0_8px_30px_rgba(0,0,0,0.04)] active:scale-[0.98] transition-all duration-500 ease-luxury border border-gray-50"
           >
              <div class="flex items-center gap-5">
                 <div class="size-14 rounded-2xl bg-[#F2F7F5] flex items-center justify-center text-[#103E32]">
                    <span class="material-symbols-rounded text-2xl">language</span>
                 </div>
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

           <!-- Change Password Button -->
           <button 
              @click="showPasswordModal = true"
              class="w-full bg-white p-7 rounded-[32px] flex items-center justify-between shadow-[0_8px_30px_rgba(0,0,0,0.04)] active:scale-[0.98] transition-all duration-500 ease-luxury border border-gray-50"
           >
              <div class="flex items-center gap-5">
                 <div class="size-14 rounded-2xl bg-[#F2F7F5] flex items-center justify-center text-[#103E32]">
                    <span class="material-symbols-rounded text-2xl">lock_reset</span>
                 </div>
                 <div class="text-left">
                    <p class="font-sans font-bold text-xl text-text-main tracking-tight">{{ lang === 'cn' ? '修改密码' : 'Change Password' }}</p>
                    <p class="text-xs text-gray-400 mt-1 font-medium tracking-wide">{{ lang === 'cn' ? '更新您的账户密码' : 'Update your account password' }}</p>
                 </div>
              </div>
              <span class="material-symbols-rounded text-gray-300">chevron_right</span>
           </button>

           <!-- Admin System Link -->
           <a 
              href="http://localhost:8080"
              target="_blank"
              class="w-full bg-gradient-to-r from-gray-900 to-gray-800 p-7 rounded-[32px] flex items-center justify-between shadow-lg shadow-gray-900/20 active:scale-[0.98] transition-all duration-500 ease-luxury border border-gray-700 block"
           >
              <div class="flex items-center gap-5">
                 <div class="size-14 rounded-2xl bg-white/10 flex items-center justify-center text-white backdrop-blur-sm">
                    <span class="material-symbols-rounded text-2xl">admin_panel_settings</span>
                 </div>
                 <div class="text-left">
                    <p class="font-sans font-bold text-xl text-white tracking-tight">{{ lang === 'cn' ? '管理后台' : 'Admin System' }}</p>
                    <p class="text-xs text-white/50 mt-1 font-medium tracking-wide">{{ lang === 'cn' ? '进入系统管理界面' : 'Access system administration' }}</p>
                 </div>
              </div>
              <span class="material-symbols-rounded text-white/50">open_in_new</span>
           </a>
           
           <!-- Sign Out -->
           <button 
              @click="handleLogout"
              class="w-full p-5 mt-6 text-center active:opacity-60 transition-opacity"
           >
              <span class="text-xs font-black uppercase tracking-[0.2em] text-[#103E32]/50 active:text-red-500 transition-colors">{{ t.signOut }}</span>
           </button>
       </div>
       
       <!-- Footer Version -->
       <div class="text-center pt-4 opacity-20">
           <p class="text-[9px] font-black uppercase tracking-widest">Coffee App v3.0</p>
       </div>
     </main>

     <!-- Edit Profile Modal -->
     <!-- 编辑资料弹窗 -->
     <div v-if="isEditing" class="fixed inset-0 z-50 flex items-end md:items-center justify-center pointer-events-none">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm pointer-events-auto transition-opacity" @click="isEditing = false"></div>
        
        <!-- Modal Content -->
        <div class="bg-white w-full md:w-[480px] rounded-t-[32px] md:rounded-[32px] p-8 relative z-10 pointer-events-auto animate-slide-up-modal pb-10">
           <div class="w-12 h-1 bg-gray-200 rounded-full mx-auto mb-8"></div>
           
           <h3 class="text-2xl font-black text-text-main mb-8">{{ lang === 'cn' ? '修改信息' : 'Edit Profile' }}</h3>
           
           <div class="space-y-6">
              <!-- Name Input -->
              <div class="space-y-2">
                 <label class="text-[10px] font-black text-gray-400 uppercase tracking-wider ml-4">{{ lang === 'cn' ? '昵称' : 'Nickname' }}</label>
                 <input 
                    class="w-full h-14 px-6 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-primary/20 font-bold text-lg"
                    v-model="editForm.name"
                 />
              </div>
              <!-- Phone Input -->
              <div class="space-y-2">
                 <label class="text-[10px] font-black text-gray-400 uppercase tracking-wider ml-4">{{ lang === 'cn' ? '手机号' : 'Phone' }}</label>
                 <input 
                    class="w-full h-14 px-6 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-primary/20 font-bold text-lg"
                    v-model="editForm.phone"
                 />
              </div>
              <!-- Email Input -->
              <div class="space-y-2">
                 <label class="text-[10px] font-black text-gray-400 uppercase tracking-wider ml-4">Email</label>
                 <input 
                    class="w-full h-14 px-6 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-primary/20 font-bold text-lg"
                    v-model="editForm.email"
                 />
              </div>
              
              <!-- Save Button -->
              <button 
                   @click="handleSaveProfile" 
                   class="w-full h-16 rounded-[24px] font-black text-white bg-[#103E32] shadow-xl shadow-[#103E32]/20 active:scale-[0.96] transition-all duration-500 ease-luxury mt-6 text-lg tracking-wide"
               >
                   {{ lang === 'cn' ? '保存' : 'Save Changes' }}
               </button>
            </div>
         </div>
      </div>

     <!-- Change Password Modal -->
     <!-- 修改密码弹窗 (使用 Teleport 挂载到 body 以确保层级正确) -->
     <Teleport to="body">
       <div v-if="showPasswordModal" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showPasswordModal = false"></div>
          
          <!-- Modal Content -->
          <div class="bg-white w-full max-w-md rounded-[32px] p-8 relative z-10 shadow-2xl animate-scale-in">
             <div class="w-12 h-1 bg-gray-200 rounded-full mx-auto mb-8"></div>
             
             <h3 class="text-2xl font-black text-[#103E32] mb-8">{{ lang === 'cn' ? '修改密码' : 'Change Password' }}</h3>
             
             <div class="space-y-6">
                <!-- Old Password -->
                <div class="space-y-2">
                   <label class="text-[10px] font-black text-gray-400 uppercase tracking-wider ml-4">{{ lang === 'cn' ? '原密码' : 'Old Password' }}</label>
                   <input 
                      class="w-full h-14 px-6 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-[#103E32]/20 font-bold text-lg text-text-main"
                      v-model="passwordForm.oldPassword"
                      type="password"
                      autocomplete="off"
                   />
                </div>
                <!-- New Password -->
                <div class="space-y-2">
                   <label class="text-[10px] font-black text-gray-400 uppercase tracking-wider ml-4">{{ lang === 'cn' ? '新密码' : 'New Password' }}</label>
                   <input 
                      class="w-full h-14 px-6 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-[#103E32]/20 font-bold text-lg text-text-main"
                      v-model="passwordForm.newPassword"
                      type="password"
                      autocomplete="new-password"
                   />
                </div>
                <!-- Confirm Password -->
                <div class="space-y-2">
                   <label class="text-[10px] font-black text-gray-400 uppercase tracking-wider ml-4">{{ lang === 'cn' ? '确认新密码' : 'Confirm Password' }}</label>
                   <input 
                      class="w-full h-14 px-6 bg-gray-50 rounded-2xl outline-none focus:ring-2 focus:ring-[#103E32]/20 font-bold text-lg text-text-main"
                      v-model="passwordForm.confirmPassword"
                      type="password"
                      autocomplete="new-password"
                   />
                </div>
                <!-- Error Msg -->
                <p v-if="passwordError" class="text-sm text-red-500 font-bold ml-4">{{ passwordError }}</p>
                
                <!-- Action Buttons -->
                <div class="flex flex-col gap-3 mt-6">
                   <button 
                        @click="handlePasswordChange" 
                        class="w-full h-16 rounded-[24px] font-black text-white bg-[#103E32] shadow-xl shadow-[#103E32]/20 active:scale-[0.96] transition-all duration-300 text-lg tracking-wide"
                    >
                        {{ lang === 'cn' ? '更新密码' : 'Update Password' }}
                    </button>
                    <button 
                        @click="showPasswordModal = false" 
                        class="w-full h-16 rounded-[24px] font-black text-[#103E32] bg-gray-100 active:scale-[0.96] transition-all duration-300 text-lg tracking-wide active:bg-gray-200"
                    >
                        {{ lang === 'cn' ? '取消' : 'Cancel' }}
                    </button>
                </div>
              </div>
           </div>
        </div>
     </Teleport>
  </div>
</template>
