<script setup lang="ts">
import { login } from '@/api/login'
import { setToken } from '@/utils/auth'
import type { FormInstance } from 'element-plus'
const route = useRoute()
const router = useRouter()
const form = reactive({ username: '', password: '' })
const formRef = ref<FormInstance>()
const busy = ref(false)
const error = ref('')
const insecureHttp = window.location.protocol === 'http:'
  && !['localhost', '127.0.0.1'].includes(window.location.hostname)
const submit = async () => {
  if (!await formRef.value?.validate().catch(() => false)) return
  busy.value = true; error.value = ''
  try { setToken(await login(form)); const redirect = String(route.query.redirect || '/'); await router.replace(redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/') }
  catch (reason: any) { error.value = reason?.message || '登录失败，请检查账号和密码' }
  finally { busy.value = false }
}
</script>
<template>
  <main class="login-page">
    <section class="login-card">
      <Icon icon="ep:coffee" :size="36"/><p class="eyebrow">OTIA CAFÉ</p><h1>管理端登录</h1>
      <p class="intro">学校管理员与店长使用账号和密码登录。</p>
      <ElAlert v-if="insecureHttp" type="warning" :closable="false" role="note" class="mb-16px" title="当前测试地址未启用 HTTPS，请勿输入真实密码。"/>
      <ElAlert v-if="error" :title="error" type="error" :closable="false" role="alert" class="mb-16px"/>
      <ElForm ref="formRef" :model="form" label-position="top" @submit.prevent="submit">
        <ElFormItem label="账号" prop="username" :rules="[{required:true,message:'请输入账号',trigger:'blur'}]"><ElInput v-model="form.username" autocomplete="username" size="large" autofocus/></ElFormItem>
        <ElFormItem label="密码" prop="password" :rules="[{required:true,message:'请输入密码',trigger:'blur'}]"><ElInput v-model="form.password" type="password" autocomplete="current-password" show-password size="large"/></ElFormItem>
        <ElButton type="primary" native-type="submit" size="large" :loading="busy" class="login-submit">登录</ElButton>
      </ElForm>
      <p class="footnote">北京外国语大学附属杭州橄榄树学校</p>
    </section>
  </main>
</template>
<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 16% 12%, rgb(255 255 255 / 54%) 0, transparent 34%),
    linear-gradient(145deg, var(--otia-sage) 0%, #e8f0e8 55%, #dce8df 100%);
}
.login-card {
  width: 100%;
  max-width: 420px;
  padding: 36px;
  background: var(--otia-card);
  border: 1px solid var(--otia-border);
  border-radius: 12px;
  box-shadow: var(--otia-shadow-lg);
}
.login-card > .iconify {
  box-sizing: content-box;
  padding: 12px;
  color: #fff;
  background: var(--otia-accent);
  border-radius: 9px;
}
.eyebrow { margin: 22px 0 8px; color: var(--otia-accent); font-size: 11px; font-weight: 700; letter-spacing: 2.6px; }
h1 { margin: 0; color: var(--otia-text); font-size: 28px; font-weight: 650; letter-spacing: -.02em; }
.intro { margin: 10px 0 24px; color: var(--otia-muted); font-size: 14px; line-height: 1.7; }
.login-submit { width: 100%; margin-top: 8px; }
.footnote { margin: 24px 0 0; color: var(--otia-muted); font-size: 12px; text-align: center; }
@media (max-width: 480px) { .login-card { padding: 30px 24px; } }
</style>
