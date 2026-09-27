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
// The form shakes once when a sign-in is refused.
const rejected = ref(false);
const reject = (message: string) => {
    toast.error(message);
    rejected.value = false;
    requestAnimationFrame(() => { rejected.value = true; });
};

const handleLogin = async () => {
    if (!username.value || !password.value) {
        reject('Please enter username and password');
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
            reject('This account has no access to the KDS');
            return;
        }
        auth.setSession(data.access_token, data.role);
        toast.success('Login successful');
        // replace: keep the sign-in page out of the back history (iPad edge swipe)
        router.replace('/');
    } catch (e) {
        reject('Login failed. Please check credentials.');
    } finally {
        loading.value = false;
    }
};

</script>

<template>
<div class="fixed inset-0 w-full h-full bg-background-light overflow-y-auto font-sans select-none flex items-center justify-center p-6">
  <div class="w-full max-w-[380px]">
    <div class="mb-14">
      <p class="eyebrow animate-slide-up-content">OTIA · Kitchen Display</p>
      <h1 class="mt-3 font-serif text-[46px] font-medium leading-none tracking-[-0.02em] text-text-main animate-text-reveal" style="animation-delay: 60ms">Barista</h1>
      <p class="mt-4 text-[15px] text-text-sub animate-slide-up-content" style="animation-delay: 120ms">Sign in to manage orders</p>
    </div>

    <form @submit.prevent="handleLogin" class="space-y-7" :class="{ shake: rejected }" @animationend="rejected = false">
      <div class="animate-slide-up-content" style="animation-delay: 180ms">
        <label for="kds-username" class="eyebrow">Username</label>
        <div class="line-field mt-1">
          <input id="kds-username" v-model="username" type="text" placeholder="Enter your username" autocomplete="username" autocapitalize="off" spellcheck="false" />
        </div>
      </div>

      <div class="animate-slide-up-content" style="animation-delay: 230ms">
        <label for="kds-password" class="eyebrow">Password</label>
        <div class="line-field mt-1">
          <input id="kds-password" v-model="password" type="password" placeholder="••••••••" autocomplete="current-password" />
        </div>
      </div>

      <div class="pt-3 animate-slide-up-content" style="animation-delay: 280ms">
        <button type="submit" :disabled="loading" class="btn btn-primary btn-lg w-full group">
          <span v-if="loading" class="size-4 border-[1.5px] border-white/30 border-t-white rounded-full animate-spin" aria-hidden="true"></span>
          <template v-else>
            Sign in
            <AppIcon name="arrow-right" class="text-base nudge" />
          </template>
        </button>
      </div>
    </form>

    <p class="mt-10 text-[12px] text-text-sub animate-fade-in" style="animation-delay: 400ms">For barista staff only.</p>
  </div>
</div>
</template>
