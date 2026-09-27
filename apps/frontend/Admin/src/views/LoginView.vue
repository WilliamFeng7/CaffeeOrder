<script setup lang="ts">
import AppIcon from '@shared/components/AppIcon.vue';
import { ref, computed, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import { auth } from '@shared/auth';

const router = useRouter();
const toast = useToastStore();
const username = ref('');
const password = ref('');
const isLoading = ref(false);

// The form shakes once when a sign-in is refused.
const rejected = ref(false);
const shake = () => {
    rejected.value = false;
    requestAnimationFrame(() => { rejected.value = true; });
};

// 动态计算学生端URL：开发环境用5173，生产环境（81端口）跳转到80端口
const studentUrl = computed(() => {
    const currentPort = window.location.port;
    if (currentPort === '81') {
        // 生产 Docker 环境：81是管理端，80是学生端
        return `${window.location.protocol}//${window.location.hostname}:80`;
    } else if (currentPort === '5174') {
        // 开发环境：5174是管理端，5173是学生端
        return `${window.location.protocol}//${window.location.hostname}:5173`;
    } else {
        // 默认: 跳转到80端口
        return `${window.location.protocol}//${window.location.hostname}:80`;
    }
});

const countdownTimer = ref<any>(null);
const countdownSeconds = ref(0);

const clearCountdown = () => {
    if (countdownTimer.value) {
        clearInterval(countdownTimer.value);
        countdownTimer.value = null;
    }
};

// Stop the lockout countdown if the user navigates away mid-lockout
onUnmounted(clearCountdown);

const handleLogin = async () => {
    if (!username.value || !password.value) {
        toast.warning('请输入用户名和密码');
        shake();
        return;
    }
    
    isLoading.value = true;
    clearCountdown();

    try {
        const res = await api.login(username.value, password.value);
        // Reject non-admin accounts *before* storing anything: the backend
        // returns `role` on the token response, so accepting a student/barista
        // session here could only produce 403s later.
        if (String(res.role).toLowerCase() !== 'admin') {
            toast.error('该账号无权访问管理后台 (Not an admin account)');
            shake();
            return;
        }
        auth.setSession(res.access_token, res.role);
        router.push('/');
    } catch (e: any) {
        // 检查是否有详细的结构化错误信息
        const detail = e.response?.data?.detail;

        if (detail && typeof detail === 'object') {
            if (detail.code === 'locked') {
                const unlockAt = new Date(detail.unlock_at);
                const now = new Date();
                let diffSeconds = Math.ceil((unlockAt.getTime() - now.getTime()) / 1000);
                
                if (diffSeconds > 0) {
                    countdownSeconds.value = diffSeconds;
                    toast.error(`账号已锁定，请等待 ${diffSeconds} 秒`);
                    
                    countdownTimer.value = setInterval(() => {
                        countdownSeconds.value--;
                        if (countdownSeconds.value <= 0) {
                            clearCountdown();
                            toast.info('锁定已解除，请重试');
                        }
                    }, 1000);
                } else {
                    toast.error(detail.message);
                }
            } else if (detail.code === 'failed') {
                const attemptsLeft = detail.attempts_left;
                 if (attemptsLeft !== null && attemptsLeft !== undefined) {
                    toast.error(`账号密码错误 (剩余 ${attemptsLeft} 次机会)`);
                } else {
                    toast.error('账号密码错误');
                }
            } else {
                 toast.error(detail.message || '登录失败');
            }
        } else {
            toast.error('账号密码错误或网络异常');
        }
        shake();
    } finally {
        isLoading.value = false;
    }
};
</script>

<template>
  <div class="fixed inset-0 bg-background-light flex items-center justify-center p-6 overflow-y-auto">
    <div class="w-full max-w-[380px]">
        <div class="mb-14">
            <p class="eyebrow animate-slide-up-content">OTIA · 管理后台</p>
            <h1 class="mt-3 font-serif text-[44px] font-medium leading-none tracking-[-0.02em] text-text-main animate-text-reveal" style="animation-delay: 60ms">管理员登录</h1>
            <p class="mt-4 text-[15px] text-text-sub animate-slide-up-content" style="animation-delay: 120ms">使用管理员账号进入系统后台</p>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-7" :class="{ shake: rejected }" @animationend="rejected = false">
            <div class="animate-slide-up-content" style="animation-delay: 180ms">
                <label for="admin-username" class="eyebrow">用户名</label>
                <div class="line-field mt-1">
                    <input id="admin-username" v-model="username" type="text" autocomplete="username" autocapitalize="off" spellcheck="false" placeholder="输入管理员账号" />
                </div>
            </div>

            <div class="animate-slide-up-content" style="animation-delay: 230ms">
                <label for="admin-password" class="eyebrow">密码</label>
                <div class="line-field mt-1">
                    <input id="admin-password" v-model="password" type="password" autocomplete="current-password" placeholder="输入密码" />
                </div>
            </div>

            <div class="pt-3 animate-slide-up-content" style="animation-delay: 280ms">
                <button type="submit" :disabled="isLoading || countdownSeconds > 0" class="btn btn-primary btn-lg w-full group">
                    <span v-if="isLoading" class="size-4 border-[1.5px] border-white/30 border-t-white rounded-full animate-spin" aria-hidden="true"></span>
                    <template v-else-if="countdownSeconds > 0">请等待 {{ countdownSeconds }} 秒</template>
                    <template v-else>
                        登录
                        <AppIcon name="arrow-right" class="text-base nudge" />
                    </template>
                </button>
            </div>
        </form>

        <a :href="studentUrl" class="link mt-10 text-[13px] text-text-sub hover:text-text-main animate-fade-in" style="animation-delay: 400ms">返回学生端</a>
    </div>
  </div>
</template>
