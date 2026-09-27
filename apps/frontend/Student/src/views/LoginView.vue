<script setup lang="ts">
/**
 * LoginView.vue
 * 
 * 登录页面视图组件 (Login View Component).
 * 
 * 核心功能 (Core Features):
 * 1. 用户认证 (User Authentication): 调用 API 获取 JWT Token。
 * 2. 输入验证 (Input Logic): 校验手机号格式 (11位数字) 或用户名。
 * 3. 错误处理 (Error Handling): 显示锁定、限流或凭证错误信息。
 * 4. 界面交互: 加载状态动画，平滑过渡效果。
 */

import AppIcon from '@shared/components/AppIcon.vue';
import { ref, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import type { Language } from '../types';
import { auth } from '@shared/auth';

const router = useRouter();

onMounted(() => {
    // 每次进入登录页，清除 Token
    auth.clearToken();
});

// 定义 Props (Props Definition)
// lang 可选: 路由不传递 props 时默认为英文 (route doesn't pass props)
const props = withDefaults(defineProps<{
  lang?: Language; // 当前语言环境
}>(), {
  lang: 'en'
});

// 定义 Events (Events Definition)
const emit = defineEmits<{
  (e: 'login-success'): void; // 登录成功回调
}>();



// --- 状态定义 (State Definitions) ---

// 用户名/手机号输入框
const toast = useToastStore();
const username = ref('');

// 密码输入框
const password = ref('');
const showPassword = ref(false);

// 登录请求加载状态
const isLoading = ref(false);

// API 返回的错误消息 (如: 账号锁定)
// const errorMsg = ref(''); // Removed in favor of Toast

// 输入框本身的格式错误提示 (如: 手机号位数不对)
const inputError = ref('');

/**
 * 实时监听用户名输入 (Real-time Validation)
 * 校验规则:
 * 1. 如果包含空格 -> 报错
 * 2. 如果纯数字但长度超过11位 -> 报错 (手机号最大11位)
 */
watch(username, (newVal) => {
   if (!newVal) {
     inputError.value = '';
     return;
   }
   
   // 检查空格
   if (/\s/.test(newVal)) {
      inputError.value = props.lang === 'cn' ? '不能包含空格' : 'No spaces allowed';
      return;
   }
   
   // 检查纯数字长度
   if (/^\d+$/.test(newVal)) {
      if (newVal.length > 11) {
          inputError.value = props.lang === 'cn' ? '手机号不能超过11位' : 'Phone number cannot exceed 11 digits';
      } else {
          inputError.value = '';
      }
   }
});

/**
 * 处理登录提交 (Handle Login Submit)
 */
// 倒计时引用
const countdownTimer = ref<number | null>(null);

// 清理定时器
const clearCountdown = () => {
    if (countdownTimer.value) {
        clearInterval(countdownTimer.value);
        countdownTimer.value = null;
    }
};

/**
 * 处理登录提交 (Handle Login Submit)
 */
const handleLogin = async () => {
  if (!username.value || !password.value) return;
  
  // 提交前的最终校验
  if (/^\d+$/.test(username.value) && username.value.length !== 11) {
      inputError.value = props.lang === 'cn' ? '请输入11位手机号' : 'Please enter an 11-digit phone number';
      return;
  }
  
  isLoading.value = true;
  inputError.value = '';
  clearCountdown();
  
  try {
    // 调用 API 获取 Token 和用户信息
    const data = await api.login(username.value, password.value);

    // 检查角色 (Check Role) - BEFORE storing anything.
    // The token used to be written to sessionStorage first and only then
    // rejected, which left a live admin session sitting in the student app's
    // storage; barista accounts were not checked at all.
    const role = String(data.role || '').toLowerCase();
    if (role !== 'student') {
      throw new Error(
        role === 'admin'
          ? '403 Admin account cannot login to Student App'
          : '403 Staff account cannot login to Student App'
      );
    }

    // 存储 Token 到本地
    auth.setSession(data.access_token, data.role);

    router.push('/');
    emit('login-success'); // 兼容旧逻辑，但在路由模式下可能不需要
    
  } catch (e: any) {
    // 错误处理逻辑 (Error Handling)
    const status = e.response?.status;
    const detail = e.response?.data?.detail;

    if (detail && typeof detail === 'object') {
        // 处理结构化错误 (Structured Error)
        if (detail.code === 'locked') {
           // 账户已锁定
           const unlockAt = new Date(detail.unlock_at);
           const now = new Date();
           const diffSeconds = Math.ceil((unlockAt.getTime() - now.getTime()) / 1000);
           
           if (diffSeconds > 0) {
               const msg = props.lang === 'cn' 
                   ? `账号已锁定，请等待 ${diffSeconds} 秒` 
                   : `Account locked. Please wait ${diffSeconds}s`;
               toast.error(msg);
           } else {
                 toast.error(detail.message);
           }

        } else if (detail.code === 'failed') {
            // 登录失败，显示剩余次数
            const attemptsLeft = detail.attempts_left;
            if (attemptsLeft !== null && attemptsLeft !== undefined) {
                const msg = props.lang === 'cn' 
                   ? `账号或密码错误 (剩余 ${attemptsLeft} 次机会)`
                   : `Invalid credentials (${attemptsLeft} attempts left)`;
                toast.error(msg);
            } else {
                toast.error(props.lang === 'cn' ? '账号或密码错误' : 'Invalid username or password');
            }
        } else {
            // 其他未知结构化错误
            toast.error(detail.message || (props.lang === 'cn' ? '登录失败' : 'Login failed'));
        }
    
    } else {
        // 传统字符串错误处理 (Legacy String Error Handling)
        if (status === 403 || (e.message && e.message.includes('403'))) {
            toast.error(detail || (props.lang === 'cn' ? '账号已锁定，请稍后重试' : 'Account locked. Please try again later.'));
        } else if (status === 429) {
            toast.error(props.lang === 'cn' ? '请求过于频繁，请稍后' : 'Too many attempts. Please wait.'); 
        } else {
            toast.error(props.lang === 'cn' ? '账号或密码错误' : 'Invalid username or password');
        }
    }

  } finally {
    isLoading.value = false;
  }
};

</script>

<template>
  <div class="fixed inset-0 z-[200] bg-background-light flex items-center justify-center p-6 overflow-y-auto">
    <div class="w-full max-w-[380px] animate-slide-up-content">

      <!-- Brand -->
      <div class="text-center mb-12">
        <AppIcon name="coffee" class="text-[32px] text-primary" />
        <h1 class="mt-4 font-serif text-[40px] font-medium leading-none tracking-[-0.015em] text-text-main">OTIA Café</h1>
        <p class="mt-3 text-[15px] text-text-sub">{{ lang === 'cn' ? '登录后开始点单' : 'Sign in to start your order' }}</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-5">
        <div>
          <label for="username" class="block text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub mb-2">{{ lang === 'cn' ? '账号' : 'Account' }}</label>
          <input
            id="username"
            name="username"
            v-model="username"
            type="text"
            autocomplete="username"
            autocapitalize="off"
            spellcheck="false"
            enterkeyhint="next"
            class="w-full min-h-[52px] px-4 rounded-tile bg-cream border border-transparent text-[16px] text-text-main outline-none transition-[background-color,border-color] duration-color focus:bg-surface-light focus:border-line placeholder:text-text-sub"
            :placeholder="lang === 'cn' ? '用户名 / 手机号 / 邮箱' : 'Username, phone or email'"
          />
          <p v-if="inputError" class="mt-2 text-[13px] text-[#B42318] animate-fade-in">{{ inputError }}</p>
        </div>

        <div>
          <label for="password" class="block text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub mb-2">{{ lang === 'cn' ? '密码' : 'Password' }}</label>
          <div class="relative">
            <input
              id="password"
              name="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              enterkeyhint="go"
              class="w-full min-h-[52px] pl-4 pr-14 rounded-tile bg-cream border border-transparent text-[16px] text-text-main outline-none transition-[background-color,border-color] duration-color focus:bg-surface-light focus:border-line placeholder:text-text-sub"
              :placeholder="lang === 'cn' ? '输入密码' : 'Enter your password'"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute right-1 top-1/2 -translate-y-1/2 size-11 rounded-full text-text-sub flex items-center justify-center active:text-text-main"
              :aria-label="showPassword ? (lang === 'cn' ? '隐藏密码' : 'Hide password') : (lang === 'cn' ? '显示密码' : 'Show password')"
            >
              <AppIcon :name="showPassword ? 'eye-slash' : 'eye'" class="text-xl" />
            </button>
          </div>
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full h-14 !mt-8 rounded-full bg-primary text-white text-[16px] font-medium flex items-center justify-center gap-2 active:bg-primary-dark disabled:opacity-70"
        >
          <span v-if="isLoading" class="size-5 border-2 border-white/30 border-t-white rounded-full animate-spin" aria-hidden="true"></span>
          <span v-else>{{ lang === 'cn' ? '登录' : 'Sign In' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>
