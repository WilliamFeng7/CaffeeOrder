<script setup lang="ts">
import AppIcon from '@shared/components/AppIcon.vue';
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import { auth } from '@shared/auth';

const username = ref('');
const password = ref('');
const loading = ref(false);
const router = useRouter();
const toast = useToastStore();

const handleLogin = async () => {
    if (!username.value || !password.value) {
        toast.error('Please enter username and password');
        return;
    }

    loading.value = true;
    try {
        const data = await api.login(username.value, password.value);
        // The KDS is a staff screen: only baristas (and admins) belong here.
        // This used to store the raw token with no role check, and it hardcoded
        // the storage key instead of using the shared TOKEN_KEY.
        const role = String(data.role || '').toLowerCase();
        if (role !== 'barista' && role !== 'admin') {
            toast.error('This account has no access to the KDS');
            return;
        }
        auth.setSession(data.access_token, data.role);
        toast.success('Login successful');
        router.push('/');
    } catch (e) {
        toast.error('Login failed. Please check credentials.');
    } finally {
        loading.value = false;
    }
};

const noiseTexture = "data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E";
</script>

<template>
<div class="fixed inset-0 w-full h-full bg-background-light overflow-hidden font-sans select-none flex items-center justify-center">
  <!-- Background Noise Texture -->
  <div class="fixed inset-0 pointer-events-none z-50 opacity-[0.04] mix-blend-overlay" :style="{ backgroundImage: `url('${noiseTexture}')` }"></div>
  
  <!-- Abstract Decorations (Student Style Gradients) -->
  <div class="absolute top-0 right-0 w-[400px] h-[400px] bg-gradient-to-br from-secondary/20 to-transparent rounded-full blur-3xl -translate-y-1/3 translate-x-1/4"></div>
  <div class="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-tr from-primary/10 to-transparent rounded-full blur-3xl translate-y-1/3 -translate-x-1/4"></div>

  <div class="w-full max-w-md p-6 md:p-8 relative z-10">
    <!-- Login Card -->
    <div class="bg-white rounded-[32px] md:rounded-[40px] p-6 md:p-8 shadow-[0_30px_80px_-20px_rgba(0,0,0,0.15)] border border-gray-100 flex flex-col gap-6 md:gap-8 animate-slide-up-content">
      
      <!-- Header -->
      <div class="text-center space-y-3">
        <!-- Logo Icon -->
        <div class="w-16 h-16 md:w-20 md:h-20 bg-primary text-secondary rounded-[20px] md:rounded-[24px] flex items-center justify-center mx-auto shadow-lg shadow-primary/25 animate-scale-in" style="animation-delay: 200ms">
          <AppIcon name="coffee" class="text-3xl md:text-4xl" />
        </div>
        
        <!-- Brand -->
        <div class="animate-slide-up-content" style="animation-delay: 300ms">
          <div class="flex items-center justify-center gap-2 mb-2">
            <span class="text-[10px] font-black text-text-sub uppercase tracking-[0.3em]">OTIA DOWNTOWN</span>
          </div>
          <h1 class="text-3xl md:text-4xl font-sans font-black text-primary tracking-tight">Barista Access</h1>
          <p class="text-text-sub text-sm mt-1">Sign in to manage orders</p>
        </div>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleLogin" class="flex flex-col gap-5 animate-slide-up-content" style="animation-delay: 400ms">
        <div class="space-y-4">
          <!-- Username Field -->
          <div class="space-y-2">
            <label class="text-[10px] font-black text-text-sub uppercase tracking-[0.15em] ml-1 flex items-center gap-2">
              <AppIcon name="user" class="text-sm opacity-50" />
              Username
            </label>
            <input 
              v-model="username"
              type="text" 
              class="w-full bg-background-light border-2 border-transparent rounded-2xl px-5 py-4 text-text-main font-semibold focus:outline-none focus:border-primary/20 focus:bg-white transition-all duration-300 placeholder:text-text-sub/40"
              placeholder="Enter your username"
              autocomplete="username"
            >
          </div>

          <!-- Password Field -->
          <div class="space-y-2">
            <label class="text-[10px] font-black text-text-sub uppercase tracking-[0.15em] ml-1 flex items-center gap-2">
              <AppIcon name="lock" class="text-sm opacity-50" />
              Password
            </label>
            <input 
              v-model="password"
              type="password" 
              class="w-full bg-background-light border-2 border-transparent rounded-2xl px-5 py-4 text-text-main font-semibold focus:outline-none focus:border-primary/20 focus:bg-white transition-all duration-300 placeholder:text-text-sub/40"
              placeholder="••••••••"
              autocomplete="current-password"
            >
          </div>
        </div>

        <!-- Submit Button -->
        <button 
          type="submit" 
          :disabled="loading"
          class="w-full bg-primary text-white font-black py-4 rounded-2xl shadow-lg shadow-primary/25 active:scale-[0.97] disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center gap-3 mt-2 relative overflow-hidden group"
        >
          <!-- Shimmer effect -->
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12 translate-x-[-200%] group-hover:animate-shimmer"></div>
          
          <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          <template v-else>
            <span class="relative z-10">Sign In</span>
            <AppIcon name="arrow-right" class="text-xl relative z-10" />
          </template>
        </button>
      </form>
      
      <!-- Footer Hint -->
      <p class="text-center text-text-sub/60 text-xs animate-fade-in" style="animation-delay: 600ms">
        KDS System for Barista Staff Only
      </p>
    </div>
  </div>
</div>
</template>
