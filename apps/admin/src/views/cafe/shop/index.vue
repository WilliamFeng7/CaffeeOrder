<script setup lang="ts">
import * as Cafe from '@/api/cafe'
import type { Shop } from '@/api/cafe'
import type { FormInstance } from 'element-plus'
import { ElMessage } from 'element-plus'
defineOptions({ name: 'CafeShop' })
const form = ref<Shop>({ open: false, banner: '', businessHours: [] })
const formRef = ref<FormInstance>()
const loading = ref(true)
const saving = ref(false)
const hoursError = ref('')
const load = async () => { loading.value = true; try { form.value = await Cafe.shop() } finally { loading.value = false } }
onMounted(load)
const save = async () => {
 if (!await formRef.value?.validate().catch(() => false)) return
 const hours = [...form.value.businessHours].sort((a,b) => a.start.localeCompare(b.start))
 if (hours.some((hour,index) => !hour.start || !hour.end || hour.start >= hour.end || (index > 0 && hours[index-1].end > hour.start))) { hoursError.value = '请填写有效的营业时段，结束时间应晚于开始时间，各时段不能重叠。'; return }
 hoursError.value = ''; saving.value = true
 try { await Cafe.saveShop({ ...form.value, businessHours: hours }); await load(); ElMessage.success('营业设置已保存') } finally { saving.value = false }
}
</script>
<template>
 <h1 class="page-heading">营业设置</h1><p class="page-description">营业开关打开，且当前时间处于营业时段内，学生才可以下单。以下时间均为北京时间。</p>
 <section class="panel" v-loading="loading" style="max-width:880px">
  <ElForm ref="formRef" :model="form" label-position="top" :disabled="saving" @submit.prevent="save">
   <ElFormItem label="营业开关"><ElSwitch v-model="form.open" active-text="打开" inactive-text="关闭" size="large"/><p class="helper">临时关店、周末或假期时可以关闭，下次营业前再打开。</p></ElFormItem>
   <ElDivider/><h2>营业时段</h2><p class="helper">每天使用相同的时段。清空全部时段后，学生暂时不能下单。</p>
   <div v-for="(hour,index) in form.businessHours" :key="index" class="hour-row"><span class="hour-label">时段 {{index+1}}</span><ElTimePicker v-model="hour.start" format="HH:mm" value-format="HH:mm" placeholder="开始时间" :aria-label="`时段 ${index+1} 开始时间`"/><span>至</span><ElTimePicker v-model="hour.end" format="HH:mm" value-format="HH:mm" placeholder="结束时间" :aria-label="`时段 ${index+1} 结束时间`"/><ElButton type="danger" text @click="form.businessHours.splice(index,1)">移除</ElButton></div>
   <p v-if="hoursError" role="alert" class="form-error">{{hoursError}}</p><ElButton class="mb-20px" :disabled="form.businessHours.length>=10" @click="form.businessHours.push({start:'',end:''})">添加营业时段</ElButton>
   <ElDivider/><ElFormItem label="公告（选填，最多 120 字）" prop="banner" :rules="[{max:120,message:'公告最多 120 字'}]"><ElInput v-model="form.banner" type="textarea" :rows="3" maxlength="120" show-word-limit placeholder="例如：今天鲜果茶已售罄，感谢理解。"/></ElFormItem>
   <ElButton type="primary" native-type="submit" :loading="saving" v-hasPermi="['cafe:shop:update']">保存营业设置</ElButton>
  </ElForm>
 </section>
</template>
<style scoped>h2 { font-size:17px; margin:0 0 10px; }.helper { color:var(--otia-muted); font-size:13px; line-height:1.7; margin:8px 0 18px; width:100%; }.hour-row { display:flex; align-items:center; gap:12px; margin-bottom:16px; }.hour-label { white-space:nowrap; color:var(--otia-text-secondary); font-size:14px; }.hour-row :deep(.el-date-editor) { width:160px; }.form-error { color:var(--el-color-danger);font-size:13px; }@media(max-width:600px){.hour-row { flex-wrap:wrap; gap:8px; padding:12px; background:var(--otia-background); border-radius:8px; }.hour-label { width:100%; }.hour-row :deep(.el-date-editor) { width:calc(50% - 20px); }} </style>
