<script setup lang="ts">
import * as Cafe from '@/api/cafe'
import type { Category, MenuItem, OptionGroup } from '@/api/cafe'
import { UploadImg } from '@/components/UploadFile'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
defineOptions({ name: 'CafeMenu' })
const tab = ref('items')
const loading = ref(false)
const saving = ref(false)
const categoryList = ref<Category[]>([])
const itemList = ref<MenuItem[]>([])
const groupList = ref<OptionGroup[]>([])
const search = ref('')
const categoryFilter = ref('')
const visibleItems = computed(() => itemList.value.filter(item => (!categoryFilter.value || item.categoryCode === categoryFilter.value) && `${item.name} ${item.nameEn}`.toLowerCase().includes(search.value.toLowerCase())))
const categoryName = (code: string) => categoryList.value.find(category => category.code === code)?.name || code
const groupNames = (ids: number[]) => ids.map(id => groupList.value.find(group => group.id === id)?.name).filter(Boolean).join('、') || '无规格'
const load = async () => { loading.value = true; try { [categoryList.value, itemList.value, groupList.value] = await Promise.all([Cafe.categories(), Cafe.menuItems(), Cafe.optionGroups()]) } finally { loading.value = false } }
onMounted(load)
const itemDialog = ref(false)
const categoryDialog = ref(false)
const groupDialog = ref(false)
const itemRef = ref<FormInstance>()
const categoryRef = ref<FormInstance>()
const groupRef = ref<FormInstance>()
const emptyItem = (): MenuItem => ({ name: '', nameEn: '', description: '', descriptionEn: '', price: 0, categoryCode: categoryList.value[0]?.code || '', imageUrl: '/static/default.png', recommended: false, enabled: true, soldOut: false, sort: 0, groupIds: [] })
const item = ref<MenuItem>(emptyItem())
const yuan = ref(0)
const category = ref<Category>({ code: '', name: '', nameEn: '', sort: 0 })
const group = ref<OptionGroup>({ name: '', nameEn: '', sort: 0, options: [] })
const defaultOption = ref(0)
const optionError = ref('')
const required = (message: string) => ({ required: true, message, trigger: 'blur' })
const itemRules: FormRules = { name: [required('请输入商品中文名')], categoryCode: [required('请选择分类')], imageUrl: [required('请上传图片或填写图片地址')] }
const categoryRules: FormRules = { name: [required('请输入分类中文名')], code: [required('请输入分类编码'), {pattern: /^[a-z][a-z0-9-]{0,29}$/, message: '使用小写字母、数字和连字符', trigger: 'blur'}] }
const openItem = (row?: MenuItem) => { item.value = row ? structuredClone(toRaw(row)) : emptyItem(); yuan.value = item.value.price / 100; itemDialog.value = true; nextTick(() => itemRef.value?.clearValidate()) }
const openCategory = (row?: Category) => { category.value = row ? { ...row } : { code: '', name: '', nameEn: '', sort: 0 }; categoryDialog.value = true; nextTick(() => categoryRef.value?.clearValidate()) }
const openGroup = (row?: OptionGroup) => { group.value = row ? structuredClone(toRaw(row)) : { name: '', nameEn: '', sort: 0, options: [{ name: '', nameEn: '', priceDelta: 0, isDefault: true, sort: 0 }] }; defaultOption.value = Math.max(0, group.value.options.findIndex(option => option.isDefault)); optionError.value = ''; groupDialog.value = true; nextTick(() => groupRef.value?.clearValidate()) }
const saveItem = async () => {
 if (!await itemRef.value?.validate().catch(() => false)) return
 if (yuan.value == null || yuan.value < 0 || yuan.value > 10000) { ElMessage.error('商品价格应为 0–10000 元'); return }
 saving.value = true
 try { await Cafe.saveItem({ ...item.value, price: Math.round(yuan.value * 100) }); itemDialog.value = false; await load(); ElMessage.success('商品已保存') } finally { saving.value = false }
}
const saveCategory = async () => {
 if (!await categoryRef.value?.validate().catch(() => false)) return
 saving.value = true
 try { await Cafe.saveCategory(category.value); categoryDialog.value = false; await load(); ElMessage.success('分类已保存') } finally { saving.value = false }
}
const saveGroup = async () => {
 if (!await groupRef.value?.validate().catch(() => false)) return
 if (group.value.options.some(option => !option.name.trim() || option.priceDelta == null || option.priceDelta < 0)) { optionError.value = '请填写每个选项的中文名及有效加价'; return }
 optionError.value = ''; saving.value = true
 try { await Cafe.saveGroup({ ...group.value, options: group.value.options.map((option, index) => ({ ...option, sort: index, isDefault: index === defaultOption.value })) }); groupDialog.value = false; await load(); ElMessage.success('规格组已保存') } finally { saving.value = false }
}
const deleteOption = (index: number) => { group.value.options.splice(index, 1); if (defaultOption.value === index) defaultOption.value = 0; else if (defaultOption.value > index) defaultOption.value-- }
const remove = async (entity: string, row: {id?: number; name: string}) => {
 try { await ElMessageBox.confirm(`确定删除“${row.name}”？`, '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }) } catch { return }
 await Cafe.removeEntity(entity, row.id!); await load(); ElMessage.success('已删除')
}
</script>
<template>
 <h1 class="page-heading">菜单管理</h1><p class="page-description">维护分类、商品与规格，让菜单的叫法和价格与收银系统保持一致。</p>
 <section class="panel" v-loading="loading">
  <ElTabs v-model="tab">
   <ElTabPane label="商品" name="items">
    <div class="toolbar"><ElInput v-model="search" placeholder="搜索中文名或英文名" clearable style="width:240px" aria-label="搜索商品"/><ElSelect v-model="categoryFilter" placeholder="全部分类" clearable style="width:180px" aria-label="按分类筛选"><ElOption v-for="entry in categoryList" :key="entry.code" :label="entry.name" :value="entry.code"/></ElSelect><ElButton type="primary" v-hasPermi="['cafe:menu:update']" @click="openItem()"><Icon icon="ep:plus"/>新增商品</ElButton></div>
    <ElTable :data="visibleItems" row-key="id" empty-text="暂无商品，请新增商品" style="width:100%">
     <ElTableColumn label="商品" min-width="230"><template #default="{row}"><div class="product-cell"><img :src="row.imageUrl" :alt="row.name" width="56" height="56" loading="lazy"/><div><strong>{{row.name}}</strong><small>{{row.nameEn}}</small></div></div></template></ElTableColumn>
     <ElTableColumn label="分类" min-width="120"><template #default="{row}">{{categoryName(row.categoryCode)}}</template></ElTableColumn>
     <ElTableColumn label="价格" min-width="100"><template #default="{row}"><span class="money">{{Cafe.money(row.price)}}</span></template></ElTableColumn>
     <ElTableColumn label="规格" min-width="140"><template #default="{row}">{{groupNames(row.groupIds)}}</template></ElTableColumn>
     <ElTableColumn label="状态" min-width="170"><template #default="{row}"><div class="tags"><ElTag :type="row.enabled ? 'success' : 'info'">{{row.enabled ? '上架' : '下架'}}</ElTag><ElTag v-if="row.soldOut" type="warning">售罄</ElTag><ElTag v-if="row.recommended">店长推荐</ElTag></div></template></ElTableColumn>
     <ElTableColumn prop="sort" label="排序" width="70"/>
     <ElTableColumn label="操作" width="140" fixed="right"><template #default="{row}"><ElButton link type="primary" v-hasPermi="['cafe:menu:update']" @click="openItem(row)">编辑</ElButton><ElButton link type="danger" v-hasPermi="['cafe:menu:update']" @click="remove('menu-item',row)">删除</ElButton></template></ElTableColumn>
    </ElTable>
   </ElTabPane>
   <ElTabPane label="分类" name="categories">
    <div class="toolbar"><ElButton type="primary" v-hasPermi="['cafe:menu:update']" @click="openCategory()">新增分类</ElButton></div>
    <ElTable :data="categoryList" empty-text="暂无分类"><ElTableColumn prop="code" label="编码"/><ElTableColumn prop="name" label="中文名"/><ElTableColumn prop="nameEn" label="英文名"/><ElTableColumn prop="sort" label="排序" width="80"/><ElTableColumn label="操作" width="140"><template #default="{row}"><ElButton link type="primary" v-hasPermi="['cafe:menu:update']" @click="openCategory(row)">编辑</ElButton><ElButton link type="danger" v-hasPermi="['cafe:menu:update']" @click="remove('category',row)">删除</ElButton></template></ElTableColumn></ElTable>
   </ElTabPane>
   <ElTabPane label="规格组和选项" name="groups">
    <div class="toolbar"><ElButton type="primary" v-hasPermi="['cafe:menu:update']" @click="openGroup()">新增规格组</ElButton><span class="page-description" style="margin:0">每组只能选一个选项。</span></div>
    <ElTable :data="groupList" empty-text="暂无规格组"><ElTableColumn prop="name" label="规格组" width="140"/><ElTableColumn prop="nameEn" label="英文名" width="160"/><ElTableColumn label="选项" min-width="280"><template #default="{row}"><div class="tags"><ElTag v-for="option in row.options" :key="option.id" :type="option.isDefault ? 'primary' : 'info'">{{option.name}}<span v-if="option.priceDelta"> +{{Cafe.money(option.priceDelta)}}</span>{{option.isDefault ? ' · 默认' : ''}}</ElTag></div></template></ElTableColumn><ElTableColumn prop="sort" label="排序" width="80"/><ElTableColumn label="操作" width="140"><template #default="{row}"><ElButton link type="primary" v-hasPermi="['cafe:menu:update']" @click="openGroup(row)">编辑</ElButton><ElButton link type="danger" v-hasPermi="['cafe:menu:update']" @click="remove('option-group',row)">删除</ElButton></template></ElTableColumn></ElTable>
   </ElTabPane>
  </ElTabs>
 </section>
 <ElDialog v-model="itemDialog" :title="item.id ? '编辑商品' : '新增商品'" width="760px" :close-on-click-modal="false">
  <ElForm ref="itemRef" :model="item" :rules="itemRules" label-position="top" :disabled="saving" @submit.prevent="saveItem">
   <div class="form-grid"><ElFormItem label="中文名" prop="name"><ElInput v-model="item.name" maxlength="100"/></ElFormItem><ElFormItem label="英文名"><ElInput v-model="item.nameEn" maxlength="100"/></ElFormItem><ElFormItem label="分类" prop="categoryCode"><ElSelect v-model="item.categoryCode"><ElOption v-for="entry in categoryList" :key="entry.code" :label="entry.name" :value="entry.code"/></ElSelect></ElFormItem><ElFormItem label="价格（元）" required><ElInputNumber v-model="yuan" :min="0" :max="10000" :precision="2" :step="1"/></ElFormItem><ElFormItem label="中文描述"><ElInput v-model="item.description" type="textarea" maxlength="1000" :rows="2"/></ElFormItem><ElFormItem label="英文描述"><ElInput v-model="item.descriptionEn" type="textarea" maxlength="1000" :rows="2"/></ElFormItem></div>
   <ElFormItem label="商品图片" prop="imageUrl"><div><UploadImg v-model="item.imageUrl" height="120px" width="160px" :disabled="saving" :file-type="['image/jpeg','image/png','image/webp','image/gif']"/><ElInput v-model="item.imageUrl" placeholder="也可填写现有图片地址" class="mt-12px" style="max-width:520px" aria-label="商品图片地址"/></div></ElFormItem>
   <ElFormItem label="规格组"><ElCheckboxGroup v-model="item.groupIds"><ElCheckbox v-for="entry in groupList" :key="entry.id" :value="entry.id">{{entry.name}}</ElCheckbox></ElCheckboxGroup><span v-if="!groupList.length">请先创建规格组</span></ElFormItem>
   <div class="form-grid"><ElFormItem label="展示状态"><div class="switches"><ElSwitch v-model="item.enabled" active-text="上架"/><ElSwitch v-model="item.soldOut" active-text="售罄"/><ElSwitch v-model="item.recommended" active-text="店长推荐"/></div></ElFormItem><ElFormItem label="排序（数字越小越靠前）"><ElInputNumber v-model="item.sort" :min="0" :precision="0"/></ElFormItem></div>
  </ElForm><template #footer><ElButton @click="itemDialog=false" :disabled="saving">取消</ElButton><ElButton type="primary" :loading="saving" @click="saveItem">保存商品</ElButton></template>
 </ElDialog>
 <ElDialog v-model="categoryDialog" :title="category.id ? '编辑分类' : '新增分类'" width="500px" :close-on-click-modal="false">
  <ElForm ref="categoryRef" :model="category" :rules="categoryRules" label-position="top" :disabled="saving"><ElFormItem label="编码（创建后不能修改）" prop="code"><ElInput v-model="category.code" :disabled="!!category.id" maxlength="30"/></ElFormItem><ElFormItem label="中文名" prop="name"><ElInput v-model="category.name" maxlength="50"/></ElFormItem><ElFormItem label="英文名"><ElInput v-model="category.nameEn" maxlength="100"/></ElFormItem><ElFormItem label="排序"><ElInputNumber v-model="category.sort" :min="0" :precision="0"/></ElFormItem></ElForm><template #footer><ElButton @click="categoryDialog=false" :disabled="saving">取消</ElButton><ElButton type="primary" :loading="saving" @click="saveCategory">保存分类</ElButton></template>
 </ElDialog>
 <ElDialog v-model="groupDialog" :title="group.id ? '编辑规格组' : '新增规格组'" width="760px" :close-on-click-modal="false">
  <ElForm ref="groupRef" :model="group" label-position="top" :disabled="saving"><div class="form-grid"><ElFormItem label="规格组中文名" prop="name" :rules="[required('请输入规格组中文名')]"><ElInput v-model="group.name" maxlength="50"/></ElFormItem><ElFormItem label="英文名"><ElInput v-model="group.nameEn" maxlength="100"/></ElFormItem></div><ElFormItem label="排序"><ElInputNumber v-model="group.sort" :min="0" :precision="0"/></ElFormItem>
   <p>选项与加价 <small>加价单位为分，100 分 = 1 元。请指定一个默认选项。</small></p>
   <ElRadioGroup v-model="defaultOption" class="option-list" aria-label="默认选项"><div v-for="(option,index) in group.options" :key="index" class="option-row"><ElRadio :value="index" :aria-label="`将选项 ${index+1} 设为默认`">默认</ElRadio><ElInput v-model="option.name" placeholder="中文名" :aria-label="`选项 ${index+1} 中文名`" maxlength="50"/><ElInput v-model="option.nameEn" placeholder="英文名" :aria-label="`选项 ${index+1} 英文名`" maxlength="100"/><ElInputNumber v-model="option.priceDelta" :min="0" :max="1000000" :precision="0" :aria-label="`选项 ${index+1} 加价（分）`"/><ElButton :disabled="group.options.length<=1 || saving" type="danger" link @click="deleteOption(index)">移除</ElButton></div></ElRadioGroup>
   <p v-if="optionError" class="form-error" role="alert">{{optionError}}</p><ElButton :disabled="group.options.length>=50 || saving" class="mt-12px" @click="group.options.push({name:'',nameEn:'',priceDelta:0,isDefault:false,sort:group.options.length})">添加选项</ElButton>
  </ElForm><template #footer><ElButton @click="groupDialog=false" :disabled="saving">取消</ElButton><ElButton type="primary" :loading="saving" @click="saveGroup">保存规格组</ElButton></template>
 </ElDialog>
</template>
<style scoped>
.product-cell { display:flex; align-items:center; gap:12px; padding:6px 0; }.product-cell img { border-radius:6px; object-fit:cover; }.product-cell strong { font-weight:550; }.product-cell small { display:block; color:var(--otia-muted); margin-top:4px; }.tags { display:flex; gap:6px; flex-wrap:wrap; }.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:0 24px; }.switches { display:flex; gap:16px; flex-wrap:wrap; }.option-list { display:flex; gap:12px; width:100%; }.option-row { display:grid; grid-template-columns:75px 1fr 1fr 140px 44px; gap:8px; width:100%; align-items:center; }.option-row .el-radio { margin-right:0; }.form-error { color:var(--el-color-danger);font-size:13px; }small { color:var(--otia-muted); }@media(max-width:600px){.form-grid { grid-template-columns:1fr; }.option-row { grid-template-columns:70px 1fr; }.option-row > :nth-child(n+3) { grid-column:2; }.option-row > :nth-child(4) { width:100%; }}
</style>
