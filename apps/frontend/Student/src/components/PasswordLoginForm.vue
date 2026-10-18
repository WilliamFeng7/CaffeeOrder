<script setup lang="ts">
import { ref } from 'vue';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import type { Language } from '../types';

const props = withDefaults(defineProps<{ lang?: Language }>(), { lang: 'en' });
const emit = defineEmits<{ (e: 'success'): void }>();
const toast = useToastStore();
const isLoading = ref(false);
const studentNo = ref('');
const password = ref('');
const inputError = ref('');

const submit = async () => {
  inputError.value = '';
  if (!/^[A-Za-z0-9_-]{1,40}$/.test(studentNo.value.trim())) {
    inputError.value = props.lang === 'cn' ? '请输入正确的学号' : 'Enter a valid student number';
    return;
  }
  if (!password.value) {
    inputError.value = props.lang === 'cn' ? '请输入密码' : 'Enter your password';
    return;
  }
  isLoading.value = true;
  try {
    await api.loginWithPassword(studentNo.value.trim(), password.value);
    password.value = '';
    emit('success');
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '登录失败，请稍后重试');
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <form class="space-y-7 animate-slide-up-content" @submit.prevent="submit">
    <div>
      <label for="student-no" class="eyebrow">{{ lang === 'cn' ? '学号' : 'Student number' }}</label>
      <div class="line-field mt-1">
        <input
          id="student-no"
          v-model.trim="studentNo"
          type="text"
          autocomplete="username"
          autocapitalize="off"
          spellcheck="false"
          placeholder="S2026001"
          :disabled="isLoading"
        />
      </div>
    </div>
    <div>
      <label for="student-password" class="eyebrow">{{ lang === 'cn' ? '密码' : 'Password' }}</label>
      <div class="line-field mt-1">
        <input
          id="student-password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          placeholder="••••••••••••"
          :disabled="isLoading"
        />
      </div>
    </div>
    <p v-if="inputError" class="text-[13px] text-danger" role="alert">{{ inputError }}</p>
    <button type="submit" :disabled="isLoading" class="btn btn-primary btn-lg w-full">
      <span
        v-if="isLoading"
        class="size-4 border-[1.5px] border-white/30 border-t-white rounded-full animate-spin"
        aria-hidden="true"
      ></span>
      <template v-else>{{ lang === 'cn' ? '账号密码登录' : 'Sign in with password' }}</template>
    </button>
    <p class="text-[12px] leading-5 text-text-sub">
      {{
        lang === 'cn'
          ? '使用学校分配的学号和密码。忘记密码请联系管理员。'
          : 'Use the student number and password assigned by your school.'
      }}
    </p>
  </form>
</template>
