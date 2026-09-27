<script setup lang="ts">
/**
 * PasswordModal.vue
 *
 * 修改密码面板 (Change password), shown in the shared BottomSheet: slides up
 * on phones, rises into the centre on iPad, drag the header down to close.
 * A rejected form shakes once.
 */
import { ref, watch } from 'vue';
import type { Language } from '../types';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import BottomSheet from './BottomSheet.vue';

const props = defineProps<{
  open: boolean;
  lang: Language;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const toast = useToastStore();

const passwordForm = ref({
   oldPassword: '',
   newPassword: '',
   confirmPassword: ''
});
const passwordError = ref('');
const shake = ref(false);

// A fresh form every time the sheet opens.
watch(() => props.open, (open) => {
   if (!open) return;
   passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' };
   passwordError.value = '';
});

const reject = (message: string) => {
   passwordError.value = message;
   shake.value = false;
   requestAnimationFrame(() => { shake.value = true; });
};

/**
 * 处理密码修改
 * 调用 API 更新密码，成功后重置表单。
 */
const handlePasswordChange = async () => {
   // 1. 基础校验 (判空、长度、一致性)
   if (!passwordForm.value.oldPassword || !passwordForm.value.newPassword || !passwordForm.value.confirmPassword) {
      reject(props.lang === 'cn' ? '请填写所有字段' : 'Please fill in all fields');
      return;
   }
   if (passwordForm.value.newPassword.length < 8) {
      reject(props.lang === 'cn' ? '新密码至少8位' : 'New password must be at least 8 characters');
      return;
   }
   if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
      reject(props.lang === 'cn' ? '两次密码不一致' : 'Passwords do not match');
      return;
   }

   try {
      // 2. API 调用
      await api.updatePassword(passwordForm.value.oldPassword, passwordForm.value.newPassword);
      // 3. 重置表单并关闭
      passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' };
      toast.success(props.lang === 'cn' ? '密码修改成功' : 'Password updated successfully');
      emit('close');
   } catch (e: any) {
      reject(e.message);
   }
};
</script>

<template>
  <BottomSheet :open="open" :title="lang === 'cn' ? '修改密码' : 'Change Password'" @close="emit('close')">
     <div class="space-y-4" :class="{ shake }" @animationend="shake = false">
        <label class="block">
           <span class="label">{{ lang === 'cn' ? '原密码' : 'Old Password' }}</span>
           <input class="field" v-model="passwordForm.oldPassword" type="password" autocomplete="current-password" />
        </label>
        <label class="block">
           <span class="label">{{ lang === 'cn' ? '新密码' : 'New Password' }}</span>
           <input class="field" v-model="passwordForm.newPassword" type="password" autocomplete="new-password" />
        </label>
        <label class="block">
           <span class="label">{{ lang === 'cn' ? '确认新密码' : 'Confirm Password' }}</span>
           <input class="field" v-model="passwordForm.confirmPassword" type="password" autocomplete="new-password" />
        </label>

        <Transition name="page">
           <p v-if="passwordError" :key="passwordError" class="text-[13px] text-danger" role="alert">{{ passwordError }}</p>
        </Transition>

        <div class="flex flex-col gap-2.5 pt-3">
           <button type="button" @click="handlePasswordChange" class="btn btn-primary btn-lg w-full">
              {{ lang === 'cn' ? '更新密码' : 'Update Password' }}
           </button>
           <button type="button" @click="emit('close')" class="btn btn-ghost btn-lg w-full">
              {{ lang === 'cn' ? '取消' : 'Cancel' }}
           </button>
        </div>
     </div>
  </BottomSheet>
</template>
