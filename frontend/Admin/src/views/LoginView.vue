<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../api';
import { useToastStore } from '../stores/toast';

const router = useRouter();
const toast = useToastStore();
const username = ref('');
const password = ref('');
const isLoading = ref(false);

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

const handleLogin = async () => {
    if (!username.value || !password.value) {
        toast.warning('请输入用户名和密码');
        return;
    }
    
    isLoading.value = true;
    clearCountdown();

    try {
        const res = await api.login(username.value, password.value);
        sessionStorage.setItem('admin_token', res.access_token);
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
    } finally {
        isLoading.value = false;
    }
};
</script>

<template>
  <div class="fixed inset-0 bg-[#051F19] flex items-center justify-center p-4">
    <!-- Abstract Background -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-[20%] -left-[10%] size-[600px] bg-[#103E32] rounded-full blur-[120px] opacity-40"></div>
        <div class="absolute bottom-[10%] right-[10%] size-[400px] bg-[#DCCA98]/20 rounded-full blur-[100px] opacity-30"></div>
    </div>

    <div class="w-full max-w-md bg-white/5 backdrop-blur-xl border border-white/10 p-10 rounded-[40px] shadow-2xl relative z-10 animate-fade-in">
         <div class="text-center mb-10">
            <div class="size-20 bg-[#103E32] rounded-3xl mx-auto flex items-center justify-center shadow-lg shadow-[#103E32]/40 mb-6">
                <span class="material-symbols-rounded text-[#DCCA98] text-4xl">admin_panel_settings</span>
            </div>
            <h1 class="text-3xl font-black text-white tracking-tight">管理员登录</h1>
            <p class="text-white/40 mt-2 font-bold text-sm tracking-widest uppercase">系统后台</p>
         </div>

         <div class="space-y-6">
            <div class="space-y-2">
                <label class="text-[10px] font-black text-[#DCCA98] uppercase tracking-[0.2em] ml-4">用户名</label>
                <input 
                    v-model="username" 
                    type="text" 
                    class="w-full h-16 bg-white/5 border border-white/10 rounded-3xl px-6 text-white text-lg font-bold outline-none focus:bg-white/10 focus:border-[#DCCA98]/50 transition-all placeholder:text-white/20"
                    placeholder="输入管理员账号"
                />
            </div>
            
            <div class="space-y-2">
                <label class="text-[10px] font-black text-[#DCCA98] uppercase tracking-[0.2em] ml-4">密码</label>
                <input 
                    v-model="password" 
                    type="password" 
                    class="w-full h-16 bg-white/5 border border-white/10 rounded-3xl px-6 text-white text-lg font-bold outline-none focus:bg-white/10 focus:border-[#DCCA98]/50 transition-all placeholder:text-white/20"
                    placeholder="输入密码"
                    @keyup.enter="handleLogin"
                />
            </div>

            <!-- Errors now shown via Toast -->

            <button 
                @click="handleLogin"
                :disabled="isLoading"
                class="w-full h-16 bg-[#DCCA98] hover:bg-[#E5D5A8] active:scale-[0.98] text-[#103E32] rounded-3xl font-black text-lg tracking-wide uppercase transition-all duration-300 shadow-xl shadow-[#DCCA98]/20 mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {{ isLoading ? '登录中...' : '登录' }}
            </button>
         </div>
         
         <div class="mt-8 text-center">
             <a :href="studentUrl" class="text-white/30 text-xs font-bold hover:text-white transition-colors">返回学生端</a>
         </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-in {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}
.animate-fade-in {
    animation: fade-in 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
</style>
