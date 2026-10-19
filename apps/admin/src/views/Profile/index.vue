<script setup lang="ts">
import { getUserProfile, updateUserPassword } from '@/api/system/user/profile'
import { validatePassword } from '@/utils/password'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'

const profile = ref<any>({})
const form = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const formRef = ref<FormInstance>()
const saving = ref(false)

onMounted(async () => {
  profile.value = await getUserProfile()
})

const save = async () => {
  if (!(await formRef.value?.validate().catch(() => false))) return
  if (form.newPassword !== form.confirmPassword) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }
  saving.value = true
  try {
    await updateUserPassword(form.oldPassword, form.newPassword)
    ElMessage.success('密码已修改')
    formRef.value?.resetFields()
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <h1 class="page-heading">个人信息</h1>
  <p class="page-description">{{ profile.nickname }} · {{ profile.username }}</p>
  <section class="panel" style="max-width: 640px">
    <h2>修改密码</h2>
    <ElForm ref="formRef" :model="form" label-position="top" @submit.prevent="save">
      <ElFormItem
        label="当前密码"
        prop="oldPassword"
        :rules="[{ required: true, message: '请输入当前密码' }]"
      >
        <ElInput v-model="form.oldPassword" type="password" autocomplete="current-password" show-password />
      </ElFormItem>
      <ElFormItem
        label="新密码"
        prop="newPassword"
        :rules="[
          { required: true, message: '请输入新密码' },
          {
            validator: (_rule, value, callback) => {
              const result = validatePassword(value)
              result === true ? callback() : callback(new Error(result))
            }
          }
        ]"
      >
        <ElInput v-model="form.newPassword" type="password" autocomplete="new-password" show-password />
      </ElFormItem>
      <ElFormItem
        label="确认新密码"
        prop="confirmPassword"
        :rules="[{ required: true, message: '请再次输入新密码' }]"
      >
        <ElInput v-model="form.confirmPassword" type="password" autocomplete="new-password" show-password />
      </ElFormItem>
      <ElButton type="primary" native-type="submit" :loading="saving">保存密码</ElButton>
    </ElForm>
  </section>
</template>
