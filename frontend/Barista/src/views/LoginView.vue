
<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../api';
import { useToastStore } from '../stores/toast';

const username = ref('');
const password = ref('');
const loading = ref(false);
const router = useRouter();
const toast = useToastStore();

const handleLogin = async () => {
    if (!username.value || !password.value) {
        toast.warning('Please enter username and password');
        return;
    }

    loading.value = true;
    try {
        const data = await api.login(username.value, password.value);
        if (data.access_token) {
            sessionStorage.setItem('coffee_access_token', data.access_token);
            toast.success('Welcome back, Barista!');
            router.push('/');
        } else {
            throw new Error('No token returned');
        }
    } catch (e: any) {
        console.error(e);
        toast.error('Login failed: ' + (e.response?.data?.detail || e.message));
    } finally {
        loading.value = false;
    }
};
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-6 bg-background-light">
      <div class="w-full max-w-sm bg-surface-light p-8 rounded-[32px] shadow-xl border border-white/50 animate-scale-in">
          <div class="text-center mb-8">
              <h1 class="text-3xl font-black text-primary font-serif italic mb-2">Barista Access</h1>
              <p class="text-gray-400 text-sm font-bold">Kitchen Display System</p>
          </div>

          <form @submit.prevent="handleLogin" class="space-y-4">
              <div>
                  <label class="block text-xs font-black text-gray-400 uppercase tracking-wider mb-2 ml-1">Username</label>
                  <input v-model="username" type="text" 
                         class="w-full bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 font-bold text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                         placeholder="Enter ID"
                         autofocus>
              </div>

              <div>
                  <label class="block text-xs font-black text-gray-400 uppercase tracking-wider mb-2 ml-1">Password</label>
                  <input v-model="password" type="password" 
                         class="w-full bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 font-bold text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                         placeholder="••••••••">
              </div>

              <button type="submit" :disabled="loading"
                      class="w-full bg-primary text-white font-black py-4 rounded-2xl shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 group disabled:opacity-70 disabled:pointer-events-none mt-6">
                  <span v-if="loading" class="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></span>
                  <span v-else>Login</span>
                  <span v-if="!loading" class="material-symbols-rounded text-lg group-hover:translate-x-1 transition-transform">arrow_forward</span>
              </button>
          </form>
      </div>
  </div>
</template>
