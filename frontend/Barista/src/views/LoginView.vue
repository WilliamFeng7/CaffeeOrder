<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../api';
import { useToastStore } from '../stores/toast';

const router = useRouter();
const toast = useToastStore();
const username = ref('');
const password = ref('');
const isLoading = ref(false);
const inputError = ref('');

onMounted(() => {
    sessionStorage.removeItem('coffee_access_token');
});

// Basic validation watch
watch(username, (newVal) => {
   if (!newVal) {
     inputError.value = '';
     return;
   }
   if (/\s/.test(newVal)) {
      inputError.value = 'No spaces allowed';
   } else {
      inputError.value = '';
   }
});

const handleLogin = async () => {
    if (!username.value || !password.value) return;

    isLoading.value = true;
    inputError.value = '';

    try {
        const data = await api.login(username.value, password.value);
        
        if (data.access_token) {
            sessionStorage.setItem('coffee_access_token', data.access_token);
            // Optionally check role if needed, but for now allow any valid user
            toast.success('Welcome back, Barista!');
            router.push('/');
        } else {
            throw new Error('No token returned');
        }
    } catch (e: any) {
        console.error(e);
        
        // Robust Error Handling copied from Student App
        const status = e.response?.status;
        const detail = e.response?.data?.detail;

        if (detail && typeof detail === 'object') {
            if (detail.code === 'locked') {
               const unlockAt = new Date(detail.unlock_at);
               const now = new Date();
               let diffSeconds = Math.ceil((unlockAt.getTime() - now.getTime()) / 1000);
               if (diffSeconds > 0) {
                   toast.error(`Account locked. Please wait ${diffSeconds}s`);
               } else {
                   toast.error(detail.message);
               }
            } else if (detail.code === 'failed') {
                const attemptsLeft = detail.attempts_left;
                if (attemptsLeft !== null && attemptsLeft !== undefined) {
                    toast.error(`Invalid credentials (${attemptsLeft} attempts left)`);
                } else {
                    toast.error('Invalid username or password');
                }
            } else {
                toast.error(detail.message || 'Login failed');
            }
        } else {
            if (status === 403 || (e.message && e.message.includes('403'))) {
                toast.error(typeof detail === 'string' ? detail : 'Account locked. Please try again later.');
            } else if (status === 429) {
                toast.error('Too many attempts. Please wait.'); 
            } else {
                toast.error('Invalid username or password');
            }
        }
    } finally {
        isLoading.value = false;
    }
};
</script>

<template>
  <div class="fixed inset-0 z-[200] bg-gradient-to-br from-[#F5F7F6] to-[#E6EBE9] flex items-center justify-center p-6 bg-texture">
    <!-- Login Card Container -->
    <div class="w-full max-w-md bg-white/80 backdrop-blur-xl rounded-[48px] shadow-[0_40px_100px_-20px_rgba(16,62,50,0.15)] p-10 md:p-14 animate-slide-up-content transform-gpu border border-white/60">
      
      <!-- Header / Logo Area -->
      <div class="text-center mb-10">
        <div class="size-24 bg-gradient-to-tr from-primary/10 to-primary/5 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-inner rotate-3 hover:rotate-6 transition-transform duration-500">
           <span class="material-symbols-rounded text-primary text-5xl drop-shadow-sm">coffee_maker</span>
        </div>
        <h1 class="text-4xl font-serif font-bold text-text-main mb-3 tracking-tight">KDS Access</h1>
        <p class="text-text-sub/80 text-sm font-medium tracking-wide">Kitchen Display System</p>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-6">
        <!-- Account Input -->
        <div>
          <label class="block text-xs font-bold uppercase text-text-sub tracking-widest mb-2 ml-4">Username</label>
          <input 
            v-model="username"
            type="text" 
            class="w-full bg-background-light border-none rounded-[24px] h-[64px] px-8 font-bold text-lg text-text-main focus:ring-2 focus:ring-[#103E32]/20 transition-all duration-300 ease-out outline-none placeholder:text-gray-300"
            placeholder="Barista ID"
            autofocus
          />
          <p v-if="inputError" class="text-xs text-red-500 font-bold ml-4 mt-2 animate-fade-in">{{ inputError }}</p>
        </div>

        <!-- Password Input -->
        <div>
          <label class="block text-xs font-bold uppercase text-text-sub tracking-widest mb-2 ml-4">Password</label>
          <input 
            v-model="password"
            type="password" 
            class="w-full bg-background-light border-none rounded-[24px] h-[64px] px-8 font-bold text-lg text-text-main focus:ring-2 focus:ring-[#103E32]/20 transition-all duration-300 ease-out outline-none placeholder:text-gray-300"
            placeholder="••••••••"
          />
        </div>

        <!-- Submit Button -->
        <button 
          type="submit" 
          :disabled="isLoading"
          class="w-full bg-[#103E32] text-white h-[72px] rounded-[32px] font-sans font-black text-xl shadow-xl shadow-[#103E32]/30 active:scale-[0.96] transition-all duration-500 ease-luxury flex items-center justify-center gap-2"
        >
          <span v-if="isLoading" class="size-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          <span v-else>Login</span>
        </button>
      </form>
    </div>
  </div>
</template>
