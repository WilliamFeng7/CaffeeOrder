<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import { auth } from '@shared/auth';

const router = useRouter();
const toast = useToastStore();
const username = ref('');
const password = ref('');
const isLoading = ref(false);

onMounted(() => {
    auth.clearToken();
});

const handleLogin = async () => {
    if (!username.value || !password.value) return;
    
    isLoading.value = true;
    try {
        const data = await api.login(username.value, password.value);
        auth.setToken(data.access_token);
        
        if (data.role !== 'barista' && data.role !== 'admin') {
            throw new Error('Access denied: Barista only');
        }
        
        toast.success(`Welcome back, ${username.value}`);
        router.push('/');
    } catch (e: any) {
        toast.error(e.response?.data?.detail?.message || 'Login failed');
    } finally {
        isLoading.value = false;
    }
};
</script>

<template>
  <div class="fixed inset-0 z-[200] bg-gradient-to-br from-[#F5F7F6] to-[#E6EBE9] flex items-center justify-center p-6 bg-texture">
    <!-- Login Card Container -->
    <div class="w-full max-w-md bg-white/80 backdrop-blur-xl rounded-[48px] shadow-[0_40px_100px_-20px_rgba(16,62,50,0.15)] p-10 md:p-14 transform-gpu border border-white/60">
      
      <!-- Header -->
      <div class="text-center mb-10">
        <div class="size-24 bg-gradient-to-tr from-primary/10 to-primary/5 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-inner rotate-3 hover:rotate-6 transition-transform duration-500">
           <span class="material-symbols-rounded text-primary text-5xl drop-shadow-sm">local_cafe</span>
        </div>
        <h1 class="text-4xl font-serif font-bold text-text-main mb-3 tracking-tight">KDS Login</h1>
        <p class="text-text-sub/80 text-sm font-medium tracking-wide">Barista Station Access</p>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label class="block text-xs font-bold uppercase text-text-sub tracking-widest mb-2 ml-4">Account</label>
          <input 
            v-model="username"
            type="text" 
            class="w-full bg-background-light border-none rounded-[24px] h-[64px] px-8 font-bold text-lg text-text-main focus:ring-2 focus:ring-[#103E32]/20 transition-all duration-300 ease-out outline-none placeholder:text-gray-300"
            placeholder="Username"
          />
        </div>

        <div>
          <label class="block text-xs font-bold uppercase text-text-sub tracking-widest mb-2 ml-4">Password</label>
          <input 
            v-model="password"
            type="password" 
            class="w-full bg-background-light border-none rounded-[24px] h-[64px] px-8 font-bold text-lg text-text-main focus:ring-2 focus:ring-[#103E32]/20 transition-all duration-300 ease-out outline-none placeholder:text-gray-300"
            placeholder="Password"
          />
        </div>

        <button 
          type="submit" 
          :disabled="isLoading"
          class="w-full bg-[#103E32] text-white h-[72px] rounded-[32px] font-sans font-black text-xl shadow-xl shadow-[#103E32]/30 active:scale-[0.96] transition-all duration-500 ease-luxury flex items-center justify-center gap-2"
        >
          <span v-if="isLoading" class="size-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          <span v-else>Sign In</span>
        </button>
      </form>
    </div>
  </div>
</template>
