<script setup lang="ts">
import * as Cafe from '@/api/cafe'
import type { Order, OrderFilter } from '@/api/cafe'
import download from '@/utils/download'
defineOptions({ name: 'CafeOrder' })
const dates = ref<string[]>([])
const filters = reactive({ status: undefined as number | undefined, student: '', posOrderNo: '' })
const applied = ref<OrderFilter>({})
const pageNo = ref(1)
const pageSize = ref(20)
const rows = ref<Order[]>([])
const total = ref(0)
const summary = ref({orderCount:0,totalPrice:0,paidAmount:0})
const loading = ref(false)
const exporting = ref(false)
const detail = ref<Order>()
const detailOpen = ref(false)
let requestVersion = 0
const load = async () => {
 const version = ++requestVersion; loading.value = true
 try {
  const [page, stats] = await Promise.all([Cafe.orders({...applied.value,pageNo:pageNo.value,pageSize:pageSize.value}),Cafe.statistics(applied.value)])
  if (version === requestVersion) { rows.value = page.list; total.value = page.total; summary.value = stats }
 } finally { if(version === requestVersion) loading.value = false }
}
const search = async () => { pageNo.value = 1; applied.value = { startDate: dates.value?.[0], endDate: dates.value?.[1], status: filters.status, student: filters.student.trim() || undefined, posOrderNo: filters.posOrderNo.trim() || undefined }; await load() }
const reset = () => { dates.value=[]; filters.status=undefined; filters.student=''; filters.posOrderNo=''; search() }
const exportExcel = async () => { exporting.value = true; try { const file = await Cafe.exportOrders(applied.value); download.excel(file, 'App订单.xlsx') } finally { exporting.value = false } }
const showDetail = (row: Order) => { detail.value=row; detailOpen.value=true }
const statusType = (status: number) => status === 30 ? 'success' : (status === 1 ? 'danger' : (status === 0 || status === 2 ? 'warning' : (status === 20 ? 'primary' : 'info')))
onMounted(search)
</script>
<template>
 <h1 class="page-heading">订单管理</h1><p class="page-description">查询 App 订单和支付记录，核对收银单号。时间均为北京时间。</p>
 <section class="panel">
  <ElForm :inline="true" label-position="top" class="order-filters" @submit.prevent="search">
   <ElFormItem label="下单日期"><ElDatePicker v-model="dates" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" style="width:280px"/></ElFormItem>
   <ElFormItem label="订单状态"><ElSelect v-model="filters.status" clearable placeholder="全部状态" style="width:180px"><ElOption v-for="(label,value) in Cafe.statusLabels" :key="value" :label="label" :value="Number(value)"/></ElSelect></ElFormItem>
   <ElFormItem label="学号或姓名"><ElInput v-model="filters.student" clearable maxlength="80" placeholder="输入学号或姓名" @keyup.enter="search"/></ElFormItem>
   <ElFormItem label="收银单号"><ElInput v-model="filters.posOrderNo" clearable maxlength="20" placeholder="输入完整收银单号" @keyup.enter="search"/></ElFormItem>
   <ElFormItem label="操作"><ElButton type="primary" native-type="submit" :loading="loading">查询</ElButton><ElButton @click="reset">重置</ElButton></ElFormItem>
  </ElForm>
 </section>
 <div class="summary" aria-live="polite"><div><span>筛选结果总单数</span><strong>{{summary.orderCount}} <small>单</small></strong></div><div><span>订单总金额</span><strong class="money">{{Cafe.money(summary.totalPrice)}}</strong></div><div><span>其中已扣款金额</span><strong class="money">{{Cafe.money(summary.paidAmount)}}</strong><small>待录单、制作中、制作完成</small></div></div>
 <section class="panel">
  <div class="toolbar"><h2>App 订单</h2><ElButton :loading="loading" @click="load">刷新</ElButton><ElButton :loading="exporting" v-hasPermi="['cafe:order:export']" @click="exportExcel"><Icon icon="ep:download"/>导出 Excel</ElButton></div>
  <ElTable :data="rows" v-loading="loading" row-key="id" empty-text="没有符合条件的 App 订单">
   <ElTableColumn label="App 订单" min-width="225"><template #default="{row}"><ElButton type="primary" link @click="showDetail(row)">{{row.orderNo}}</ElButton><small class="subline">{{row.cupCount}} 杯 · {{row.studentName}}（{{row.studentNo}}）</small></template></ElTableColumn>
   <ElTableColumn label="状态" min-width="90"><template #default="{row}"><ElTag :type="statusType(row.status)">{{Cafe.statusLabels[row.status]}}</ElTag></template></ElTableColumn>
   <ElTableColumn prop="posOrderNo" label="收银单号" min-width="100"><template #default="{row}">{{row.posOrderNo || '—'}}</template></ElTableColumn>
   <ElTableColumn label="金额" min-width="80"><template #default="{row}"><span class="money">{{Cafe.money(row.totalPrice)}}</span></template></ElTableColumn>
   <ElTableColumn label="下单时间" min-width="145"><template #default="{row}"><span class="time-cell">{{Cafe.beijingTime(row.createTime)}}</span></template></ElTableColumn>
   <ElTableColumn label="回填时间" min-width="145"><template #default="{row}"><span class="time-cell">{{Cafe.beijingTime(row.enteredTime)}}</span></template></ElTableColumn>
   <ElTableColumn label="制作完成时间" min-width="145"><template #default="{row}"><span class="time-cell">{{Cafe.beijingTime(row.doneTime)}}</span></template></ElTableColumn>
   <ElTableColumn label="操作" width="60" fixed="right"><template #default="{row}"><ElButton link type="primary" @click="showDetail(row)">详情</ElButton></template></ElTableColumn>
  </ElTable>
  <div class="pagination"><ElPagination v-model:current-page="pageNo" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50,100]" layout="total, sizes, prev, pager, next" @current-change="load" @size-change="pageNo=1;load()"/></div>
 </section>
 <ElDialog v-model="detailOpen" title="App 订单详情" width="760px">
  <template v-if="detail"><ElDescriptions :column="2" border><ElDescriptionsItem label="App 订单号" :span="2">{{detail.orderNo}}</ElDescriptionsItem><ElDescriptionsItem label="姓名">{{detail.studentName}}</ElDescriptionsItem><ElDescriptionsItem label="学号">{{detail.studentNo}}</ElDescriptionsItem><ElDescriptionsItem label="状态">{{Cafe.statusLabels[detail.status]}}</ElDescriptionsItem><ElDescriptionsItem label="收银单号">{{detail.posOrderNo || '—'}}</ElDescriptionsItem><ElDescriptionsItem label="订单金额">{{Cafe.money(detail.totalPrice)}}</ElDescriptionsItem><ElDescriptionsItem label="下单时间">{{Cafe.beijingTime(detail.createTime)}}</ElDescriptionsItem><ElDescriptionsItem label="回填时间">{{Cafe.beijingTime(detail.enteredTime)}}</ElDescriptionsItem><ElDescriptionsItem label="制作完成时间">{{Cafe.beijingTime(detail.doneTime)}}</ElDescriptionsItem></ElDescriptions><ElAlert v-if="detail.failureReason" :title="detail.failureReason" :type="detail.status===1?'error':'warning'" :closable="false" class="mt-16px"/>
   <h3>商品快照</h3><div v-for="(item,index) in detail.items" :key="index" class="order-item"><img :src="item.imageUrl" :alt="item.name" width="56" height="56"/><div><strong>{{item.name}} × {{item.quantity}}</strong><small>{{item.optionsText || '无规格'}}</small></div><span class="money">{{Cafe.money(item.unitPrice * item.quantity)}}</span></div>
  </template><template #footer><ElButton @click="detailOpen=false">关闭</ElButton></template>
 </ElDialog>
</template>
<style scoped>
.order-filters { display:grid; grid-template-columns:280px 160px minmax(140px,1fr) minmax(140px,1fr) auto; gap:16px; align-items:end; }.order-filters :deep(.el-form-item) { margin-right:0; margin-bottom:0; }.order-filters :deep(.el-form-item__content) { width:100%; }.order-filters :deep(.el-input), .order-filters :deep(.el-select) { width:100% !important; }.summary { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:20px; }.summary > div { background:#fff; border:1px solid var(--otia-border); border-radius:10px; padding:20px 24px; }.summary span,.summary small { display:block; color:var(--otia-muted); font-size:13px; }.summary strong { display:block; font-size:28px; font-weight:650; color:var(--otia-text); margin:10px 0 4px; }.summary strong small { display:inline; }.toolbar h2 { font-size:17px; margin:0 auto 0 0; }.time-cell { white-space:nowrap; font-variant-numeric:tabular-nums; }.subline { display:block; color:var(--otia-muted); margin-top:4px; }.pagination { margin-top:24px; display:flex; justify-content:flex-end; overflow-x:auto; }.order-item { display:flex; align-items:center; gap:14px; padding:14px 0; border-bottom:1px solid var(--otia-border); }.order-item img { object-fit:cover; border-radius:6px; }.order-item small { display:block; margin-top:6px; color:var(--otia-muted); }.order-item > span { margin-left:auto; }@media(max-width:1200px){.order-filters { grid-template-columns:repeat(2,minmax(0,1fr)); }.order-filters :deep(.el-date-editor) { width:100% !important; }}@media(max-width:600px){.order-filters { grid-template-columns:1fr; }.summary { grid-template-columns:1fr; gap:8px; }.summary > div { padding:14px 18px; }.summary strong { font-size:23px; }.order-filters :deep(.el-form-item) { margin-right:0; width:100%; }.order-filters :deep(.el-date-editor) { width:100% !important; }}
</style>
