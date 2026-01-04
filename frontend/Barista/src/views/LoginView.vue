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
        toast.error('Please enter username and password');
        return;
    }

    loading.value = true;
    try {
        const data = await api.login(username.value, password.value);
        sessionStorage.setItem('coffee_access_token', data.access_token);
        toast.success('Login successful');
        router.push('/');
    } catch (e) {
        toast.error('Login failed. Please check credentials.');
    } finally {
        loading.value = false;
    }
};
</script>

<template>
<div class="min-h-screen flex items-center justify-center bg-texture bg-primary fixed inset-0">
     <!-- Abstract Decoration -->
    <div class="absolute top-0 right-0 w-[500px] h-[500px] bg-secondary/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
    <div class="absolute bottom-0 left-0 w-[500px] h-[500px] bg-secondary/5 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2"></div>

    <div class="w-full max-w-md p-8 relative z-10">
        <div class="bg-surface-light/95 backdrop-blur-xl rounded-[40px] p-8 shadow-2xl border border-white/50 flex flex-col gap-8 animate-slide-up-modal">
            
            <!-- Header -->
            <div class="text-center space-y-2">
                <div class="w-16 h-16 bg-primary text-secondary rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary/30">
                    <span class="material-symbols-rounded text-3xl">coffee_maker</span>
                </div>
                <h1 class="text-2xl font-serif font-bold text-text-main">Barista Access</h1>
                <p class="text-text-sub text-sm">Sign in to manage orders</p>
            </div>

            <!-- Form -->
            <form @submit.prevent="handleLogin" class="flex flex-col gap-5">
                <div class="space-y-4">
                    <div class="space-y-1">
                        <label class="text-xs font-bold text-text-sub uppercase tracking-wider ml-1">Username</label>
                        <input 
                            v-model="username"
                            type="text" 
                            class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-text-main focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all font-sans"
                            placeholder="Enter your username"
                        >
                    </div>

                    <div class="space-y-1">
                         <label class="text-xs font-bold text-text-sub uppercase tracking-wider ml-1">Password</label>
                        <input 
                            v-model="password"
                            type="password" 
                            class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-text-main focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all font-sans"
                            placeholder="••••••••"
                        >
                    </div>
                </div>

                <button 
                    type="submit" 
                    :disabled="loading"
                    class="w-full bg-primary text-secondary font-bold py-4 rounded-xl shadow-xl shadow-primary/30 hover:bg-primary/90 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 mt-2"
                >
                    <span v-if="loading" class="w-5 h-5 border-2 border-secondary/30 border-t-secondary rounded-full animate-spin"></span>
                    <span v-else>Sign In</span>
                </button>
            </form>
        </div>
    </div>
</div>
</template>
