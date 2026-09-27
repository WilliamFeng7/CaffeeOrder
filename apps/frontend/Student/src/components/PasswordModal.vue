<script setup lang="ts">
import { ref } from 'vue';
import type { Language } from '../types';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import { useSheetDrag } from '../composables/useSheetDrag';

const props = defineProps<{
  lang: Language;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const toast = useToastStore();

// 顶部的小横条可以往下拖来关闭
const sheetEl = ref<HTMLElement | null>(null);
const backdropEl = ref<HTMLElement | null>(null);
const { handlers: dragHandlers } = useSheetDrag({
  sheet: sheetEl,
  backdrop: backdropEl,
  onDismiss: () => emit('close'),
});
const passwordForm = ref({
   oldPassword: '',
   newPassword: '',
   confirmPassword: ''
});
const passwordError = ref('');

/**
 * 处理密码修改
 * 调用 API 更新密码，成功后重置表单。
 */
const handlePasswordChange = async () => {
   // 1. 基础校验 (判空、长度、一致性)
   if (!passwordForm.value.oldPassword || !passwordForm.value.newPassword || !passwordForm.value.confirmPassword) {
      passwordError.value = props.lang === 'cn' ? '请填写所有字段' : 'Please fill in all fields';
      return;
   }
   if (passwordForm.value.newPassword.length < 8) {
      passwordError.value = props.lang === 'cn' ? '新密码至少8位' : 'New password must be at least 8 characters';
      return;
   }
   if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
      passwordError.value = props.lang === 'cn' ? '两次密码不一致' : 'Passwords do not match';
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
      passwordError.value = e.message;
   }
};
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
       <!-- Backdrop -->
       <div ref="backdropEl" class="absolute inset-0 bg-black/35 animate-fade-in" @click="emit('close')"></div>
       
       <!-- Modal Content -->
       <div ref="sheetEl" role="dialog" aria-modal="true" class="bg-surface-light w-full max-w-md rounded-sheet px-6 pt-2 pb-7 relative z-10 shadow-float animate-scale-in">
          <!-- Drag handle: swipe down to close -->
          <div class="touch-none -mx-6 px-6 pt-2 pb-6" v-on="dragHandlers">
             <div class="w-9 h-1 bg-line rounded-full mx-auto mb-5" aria-hidden="true"></div>
             <h3 class="font-serif text-[24px] font-medium text-text-main">{{ lang === 'cn' ? '修改密码' : 'Change Password' }}</h3>
          </div>
          
          <div class="space-y-4">
             <!-- Old Password -->
             <div>
                <label class="block text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub mb-2">{{ lang === 'cn' ? '原密码' : 'Old Password' }}</label>
                <input 
                   class="w-full min-h-[52px] px-4 rounded-tile bg-cream border border-transparent text-[16px] text-text-main outline-none transition-[background-color,border-color] duration-color focus:bg-surface-light focus:border-line placeholder:text-text-sub"
                   v-model="passwordForm.oldPassword"
                   type="password"
                   autocomplete="current-password"
                />
             </div>
             <!-- New Password -->
             <div>
                <label class="block text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub mb-2">{{ lang === 'cn' ? '新密码' : 'New Password' }}</label>
                <input 
                   class="w-full min-h-[52px] px-4 rounded-tile bg-cream border border-transparent text-[16px] text-text-main outline-none transition-[background-color,border-color] duration-color focus:bg-surface-light focus:border-line placeholder:text-text-sub"
                   v-model="passwordForm.newPassword"
                   type="password"
                   autocomplete="new-password"
                />
             </div>
             <!-- Confirm Password -->
             <div>
                <label class="block text-[12px] font-medium tracking-[0.14em] uppercase text-text-sub mb-2">{{ lang === 'cn' ? '确认新密码' : 'Confirm Password' }}</label>
                <input 
                   class="w-full min-h-[52px] px-4 rounded-tile bg-cream border border-transparent text-[16px] text-text-main outline-none transition-[background-color,border-color] duration-color focus:bg-surface-light focus:border-line placeholder:text-text-sub"
                   v-model="passwordForm.confirmPassword"
                   type="password"
                   autocomplete="new-password"
                />
             </div>
             <!-- Error Msg -->
             <p v-if="passwordError" class="text-[13px] text-[#B42318]">{{ passwordError }}</p>
             
             <!-- Action Buttons -->
             <div class="flex flex-col gap-2.5 pt-2">
                <button 
                     type="button"
                     @click="handlePasswordChange" 
                     class="w-full h-14 rounded-full bg-primary text-white text-[16px] font-medium active:bg-primary-dark"
                 >
                     {{ lang === 'cn' ? '更新密码' : 'Update Password' }}
                 </button>
                 <button 
                     type="button"
                     @click="emit('close')" 
                     class="w-full h-14 rounded-full border border-line text-text-main text-[16px] font-medium active:bg-cream"
                 >
                     {{ lang === 'cn' ? '取消' : 'Cancel' }}
                 </button>
             </div>
           </div>
        </div>
     </div>
  </Teleport>
</template>
