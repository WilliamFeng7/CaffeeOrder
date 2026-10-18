<script setup lang="ts">
/** 钉钉自动免登；不可用时自动切换为学号密码登录。 */
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import type { Language } from '../types';
import PasswordLoginForm from '../components/PasswordLoginForm.vue';

const props = withDefaults(defineProps<{ lang?: Language }>(), { lang: 'en' });
const emit = defineEmits<{ (e: 'login-success'): void }>();
const router = useRouter();
const toast = useToastStore();
const inDingTalk = api.isDingTalk();
const insecureHttp = window.location.protocol === 'http:'
  && !['localhost', '127.0.0.1'].includes(window.location.hostname);
const isLoading = ref(inDingTalk);
const showPassword = ref(!inDingTalk);
const passwordLoginEnabled = ref(true);
const dingtalkError = ref('');

const succeed = async () => {
  await router.replace('/');
  emit('login-success');
};

const usePasswordLogin = () => {
  dingtalkError.value = '';
  showPassword.value = true;
};

const handleDingTalkLogin = async (corpId?: string) => {
  dingtalkError.value = '';
  isLoading.value = true;
  try {
    await api.loginWithDingTalk(corpId);
    await succeed();
  } catch (error) {
    const message = error instanceof Error ? error.message : '钉钉登录失败，请稍后重试';
    dingtalkError.value = message;
    if (passwordLoginEnabled.value) {
      showPassword.value = true;
    } else {
      toast.error(message);
    }
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  try {
    const config = await api.getAuthConfig();
    passwordLoginEnabled.value = config.passwordLoginEnabled;
    if (inDingTalk) {
      void handleDingTalkLogin(config.corpId);
    } else {
      showPassword.value = config.passwordLoginEnabled;
    }
  } catch (error) {
    if (inDingTalk) {
      dingtalkError.value = error instanceof Error ? error.message : '无法读取登录配置';
      showPassword.value = passwordLoginEnabled.value;
    }
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="fixed inset-0 z-[200] bg-background-light flex items-center justify-center p-6 overflow-y-auto">
    <div class="w-full max-w-[380px]">
      <div class="mb-14">
        <p class="eyebrow animate-slide-up-content">{{ lang === 'cn' ? '欢迎回来' : 'Welcome back' }}</p>
        <h1 class="mt-3 font-serif text-[46px] font-normal leading-none tracking-[-0.02em] text-text-main animate-text-reveal" style="animation-delay: 60ms">OTIA Café</h1>
        <p class="mt-4 text-[15px] text-text-sub animate-slide-up-content" style="animation-delay: 120ms">{{ lang === 'cn' ? '登录后开始点单' : 'Sign in to start your order' }}</p>
        <p v-if="insecureHttp" class="mt-4 rounded-tile bg-danger-soft px-4 py-3 text-[13px] leading-relaxed text-danger" role="note">
          {{ lang === 'cn' ? '当前测试地址未启用 HTTPS，请勿输入真实密码。' : 'This test address is not using HTTPS. Do not enter a real password.' }}
        </p>
      </div>

      <PasswordLoginForm
        v-if="showPassword && passwordLoginEnabled"
        :lang="props.lang"
        @success="succeed"
      />

      <div v-else-if="inDingTalk" class="animate-slide-up-content">
        <p class="flex items-center gap-3 text-[15px] text-text-sub">
          <span v-if="isLoading" class="size-4 border-[1.5px] border-text-sub/30 border-t-text-main rounded-full animate-spin" aria-hidden="true"></span>
          {{ isLoading ? (lang === 'cn' ? '正在通过钉钉登录…' : 'Signing in with DingTalk…') : (dingtalkError || (lang === 'cn' ? '钉钉登录未完成' : 'DingTalk sign-in was not completed')) }}
        </p>
        <button v-if="!isLoading" type="button" class="mt-6 btn btn-primary btn-lg w-full" @click="handleDingTalkLogin()">
          {{ lang === 'cn' ? '重新登录' : 'Try again' }}
        </button>
        <button
          v-if="passwordLoginEnabled"
          type="button"
          class="mt-4 w-full text-[13px] text-text-sub underline underline-offset-4"
          @click="usePasswordLogin"
        >
          {{ lang === 'cn' ? '改用账号密码登录' : 'Use student number and password' }}
        </button>
      </div>

      <div v-else class="animate-slide-up-content">
        <p class="font-serif text-[26px] text-text-main">请在钉钉中打开 OTIA Café</p>
        <p class="mt-3 text-[14px] text-text-sub">Please open OTIA Café in DingTalk.</p>
      </div>

      <button
        v-if="showPassword && inDingTalk"
        type="button"
        class="mt-8 w-full text-[13px] text-text-sub underline underline-offset-4"
        :disabled="isLoading"
        @click="handleDingTalkLogin()"
      >
        {{ lang === 'cn' ? '重新尝试钉钉登录' : 'Try DingTalk sign-in again' }}
      </button>
    </div>
  </div>
</template>
