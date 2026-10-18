<script setup lang="ts">
/**
 * 咖啡师账号登录（和管理端账号是分开的两套，见 docs/architecture.md）。
 * 登录成功后马上拉一次看板确认权限，没权限的账号不留令牌（见 api.ts 的 login）。
 */
import { ref } from 'vue';
import { YudaoError } from '@shared/yudao-client';
import AppIcon from '@shared/components/AppIcon.vue';
import { lastUsername, login, signInNotice } from '../api';

const username = ref(lastUsername());
const password = ref('');
const loading = ref(false);
/** 直接显示在表单上方的错误，后端的中文提示原样给咖啡师看。 */
const failure = ref('');
// 被拒绝时表单摇头一次。
const rejected = ref(false);
const reject = (message: string) => {
    failure.value = message;
    rejected.value = false;
    requestAnimationFrame(() => { rejected.value = true; });
};

async function handleLogin() {
    if (!username.value.trim() || !password.value) {
        reject('请输入账号和密码');
        return;
    }
    loading.value = true;
    failure.value = '';
    try {
        await login(username.value.trim(), password.value);
    } catch (error) {
        reject(error instanceof YudaoError ? error.msg : '登录失败，请重试');
    } finally {
        loading.value = false;
    }
}
</script>

<template>
<div class="fixed inset-0 w-full h-full bg-background-light overflow-y-auto select-none flex items-center justify-center p-6">
  <div class="w-full max-w-[380px]">
    <div class="mb-12">
      <p class="eyebrow animate-slide-up-content">OTIA Café</p>
      <h1 class="mt-3 font-serif text-[46px] font-medium leading-none tracking-[-0.02em] text-text-main animate-text-reveal" style="animation-delay: 60ms">咖啡师端</h1>
      <p class="mt-4 text-[15px] text-text-sub animate-slide-up-content" style="animation-delay: 120ms">登录后开始录单和制作</p>
    </div>

    <!-- 令牌被后端收回后回到这个页面，告诉咖啡师为什么又要登录 -->
    <p v-if="signInNotice" class="mb-6 text-[14px] text-warning animate-fade-in">{{ signInNotice }}</p>

    <form @submit.prevent="handleLogin" class="space-y-7" :class="{ shake: rejected }" @animationend="rejected = false">
      <div class="animate-slide-up-content" style="animation-delay: 180ms">
        <label for="username" class="eyebrow">账号</label>
        <div class="line-field mt-1" :class="{ 'is-invalid': failure }">
          <input id="username" v-model="username" type="text" placeholder="咖啡师账号" autocomplete="username" autocapitalize="off" spellcheck="false" />
        </div>
      </div>

      <div class="animate-slide-up-content" style="animation-delay: 230ms">
        <label for="password" class="eyebrow">密码</label>
        <div class="line-field mt-1" :class="{ 'is-invalid': failure }">
          <input id="password" v-model="password" type="password" placeholder="••••••••" autocomplete="current-password" />
        </div>
      </div>

      <p v-if="failure" class="text-[14px] text-danger animate-fade-in" role="alert">{{ failure }}</p>

      <div class="pt-3 animate-slide-up-content" style="animation-delay: 280ms">
        <button type="submit" :disabled="loading" class="btn btn-primary btn-lg w-full group">
          <span v-if="loading" class="size-4 border-[1.5px] border-white/30 border-t-white rounded-full animate-spin" aria-hidden="true"></span>
          <template v-else>
            登录
            <AppIcon name="arrow-right" class="text-base nudge" />
          </template>
        </button>
      </div>
    </form>

    <p class="mt-10 text-[12px] text-text-sub animate-fade-in" style="animation-delay: 400ms">只有咖啡师账号能登录，和管理端账号不通用。</p>
  </div>
</div>
</template>
