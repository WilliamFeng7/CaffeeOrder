<script setup lang="ts">
import AppIcon from '@shared/components/AppIcon.vue';
import AppModal from '@shared/components/AppModal.vue';
import AppSwitch from '@shared/components/AppSwitch.vue';
import { pinLeaving } from '@shared/list';
import { ref, onMounted, computed } from 'vue';
import { api } from '../api';
import { useToastStore } from '../stores/toast';

const products = ref<any[]>([]);
const loading = ref(true);
const showModal = ref(false);
const editingProduct = ref<any>(null); // If null, means creating new
const searchQuery = ref('');
const toast = useToastStore();

const fetchProducts = async () => {
    loading.value = true;
    try {
        products.value = await api.getProducts();
    } catch (e: any) {
        console.error(e);
        toast.error('加载商品失败: ' + (e.response?.data?.detail || e.message));
    } finally {
        loading.value = false;
    }
};

const filteredProducts = computed(() => {
    if (!searchQuery.value) return products.value;
    const lower = searchQuery.value.toLowerCase();
    return products.value.filter(p => 
        p.name.toLowerCase().includes(lower) || 
        p.category.toLowerCase().includes(lower)
    );
});

const handleCreate = () => {
    editingProduct.value = { 
        name: '', 
        price: 0, 
        category: 'coffee', 
        description: '',
        image: '', // URL
        is_recommend: false,
        inventory_count: 999, // Default stock, 0 means sold out
        is_active: true
    };
    showModal.value = true;
};

const handleEdit = (prod: any) => {
    editingProduct.value = { ...prod };
    showModal.value = true;
};

const showDeleteModal = ref(false);
const deleteId = ref<number | null>(null);

const handleDelete = (id: number) => {
    deleteId.value = id;
    showDeleteModal.value = true;
};

const deleteName = computed(() => products.value.find(p => p.id === deleteId.value)?.name ?? '');

const CATEGORY_LABEL: Record<string, string> = { seasonal: '当季', coffee: '咖啡', fruit: '果茶', bakery: '烘焙' };
const categoryLabel = (c: string) => CATEGORY_LABEL[c] ?? c;

const confirmDelete = async () => {
    if (deleteId.value) {
        await api.deleteProduct(deleteId.value);
        showDeleteModal.value = false;
        fetchProducts();
    }
};

const handleSave = async () => {
    if (!editingProduct.value) return;
    
    // Validate
    if (!editingProduct.value.name || editingProduct.value.price <= 0) {
        toast.warning('请填写有效的名称和价格');
        return;
    }

    try {
        if (editingProduct.value.id) {
            await api.updateProduct(editingProduct.value.id, editingProduct.value);
        } else {
            await api.createProduct(editingProduct.value);
        }
        showModal.value = false;
        fetchProducts();
    } catch (e: any) {
        console.error(e);
        let msg = e.response?.data?.detail || e.message;
        if (typeof msg === 'object') {
             msg = JSON.stringify(msg);
        }
        toast.error('保存失败: ' + msg);
    }
};

const handleFileUpload = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files[0]) {
        try {
            const url = await api.uploadImage(target.files[0]);
            editingProduct.value.image = url;
            toast.success('上传成功');
        } catch (e) {
            toast.error('上传失败');
        }
    }
};

// The first load cascades in; after that, cards entering or leaving (search,
// create, delete) use the list transition instead.
const settled = ref(false);
onMounted(async () => {
    await fetchProducts();
    window.setTimeout(() => { settled.value = true; }, 1000);
});
</script>

<template>
  <div class="space-y-6">
     <div class="flex flex-wrap items-end justify-between gap-4 animate-slide-up-content">
         <div>
             <p class="eyebrow">{{ products.length }} 款商品</p>
             <h1 class="mt-2 font-serif text-[34px] font-medium leading-tight tracking-[-0.015em]">商品管理</h1>
         </div>

         <div class="flex items-center gap-3 w-full md:w-auto">
             <label class="relative flex-1 md:w-64">
                 <span class="sr-only">搜索商品</span>
                 <AppIcon name="search" weight="light" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-lg text-text-sub pointer-events-none" />
                 <input v-model="searchQuery" type="text" placeholder="搜索名称或分类" class="field !h-10 !rounded-full pl-10" />
             </label>
             <button type="button" @click="handleCreate" class="btn btn-primary btn-sm shrink-0">
                 <AppIcon name="plus" class="text-base" />
                 添加商品
             </button>
         </div>
     </div>

     <!-- Products -->
     <TransitionGroup tag="div" name="list" class="relative grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" :class="{ 'stagger-in': !settled }" @before-leave="pinLeaving">
         <article
             v-for="prod in filteredProducts"
             :key="prod.id"
             class="group card p-4 flex gap-4 hover:border-line-strong transition-colors duration-color"
         >
             <!-- Image -->
             <div class="relative size-[88px] rounded-tile bg-cream bg-cover bg-center shrink-0 overflow-hidden" :class="{ 'grayscale opacity-60': prod.inventory_count <= 0 }" :style="{ backgroundImage: `url(${prod.image || '/coffee-cup.png'})` }"></div>

             <div class="flex-1 min-w-0 flex flex-col">
                 <div class="flex items-start justify-between gap-2">
                     <div class="min-w-0">
                         <p class="eyebrow !text-[10px]">
                             {{ categoryLabel(prod.category) }}
                             <span v-if="prod.is_recommend" class="ml-1 !text-secondary-content">· 推荐</span>
                         </p>
                         <h3 class="mt-1 text-[15px] font-medium truncate">{{ prod.name }}</h3>
                     </div>
                     <span v-if="prod.inventory_count <= 0" class="chip chip-danger shrink-0">售罄</span>
                 </div>
                 <p class="mt-1 text-[12px] text-text-sub line-clamp-1">{{ prod.description }}</p>

                 <div class="mt-auto pt-2 flex items-end justify-between gap-2">
                     <div class="flex items-baseline gap-2">
                         <span class="font-serif text-[18px] font-medium tabular-nums">¥{{ prod.price.toFixed(2) }}</span>
                         <span class="text-[12px] text-text-sub tabular-nums">库存 {{ prod.inventory_count }}</span>
                     </div>

                     <!-- Hidden until hover with a mouse; always shown on touch, where hover never happens -->
                     <div class="flex gap-1 opacity-100 [@media(hover:hover)_and_(pointer:fine)]:opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity duration-color">
                         <button type="button" @click="handleEdit(prod)" aria-label="编辑" title="编辑" class="icon-btn size-8 [@media(pointer:coarse)]:size-11">
                             <AppIcon name="edit" weight="light" class="text-[18px]" />
                         </button>
                         <button type="button" @click="handleDelete(prod.id)" aria-label="删除" title="删除" class="icon-btn size-8 [@media(pointer:coarse)]:size-11 hover:!text-danger hover:!bg-danger-soft">
                             <AppIcon name="trash" weight="light" class="text-[18px]" />
                         </button>
                     </div>
                 </div>
             </div>
         </article>
     </TransitionGroup>

     <div v-if="filteredProducts.length === 0 && !loading" class="py-20 flex flex-col items-center gap-2 text-text-sub animate-fade-in">
         <AppIcon name="package" weight="light" class="text-3xl" />
         <p class="text-[13px]">暂无商品</p>
     </div>

     <!-- Edit / create -->
     <AppModal :open="showModal" size="lg" :title="editingProduct?.id ? '编辑商品' : '添加商品'" @close="showModal = false">
         <div v-if="editingProduct" class="space-y-5">
             <label class="block">
                 <span class="label">商品名称</span>
                 <input v-model="editingProduct.name" class="field" placeholder="例如：拿铁" />
             </label>
             <div class="grid grid-cols-2 gap-4">
                 <label class="block">
                     <span class="label">价格 (¥)</span>
                     <input v-model.number="editingProduct.price" type="number" step="0.5" class="field tabular-nums" />
                 </label>
                 <label class="block">
                     <span class="label">分类</span>
                     <select v-model="editingProduct.category" class="field">
                         <option value="seasonal">当季特供</option>
                         <option value="coffee">咖啡</option>
                         <option value="fruit">果茶</option>
                         <option value="bakery">烘焙</option>
                     </select>
                 </label>
             </div>

             <div>
                 <span class="label">商品图片</span>
                 <div class="flex gap-4 items-center">
                     <div class="size-20 rounded-tile bg-cream bg-cover bg-center shrink-0 border border-line" :style="{ backgroundImage: `url(${editingProduct.image || '/coffee-cup.png'})` }"></div>
                     <div class="flex-1 min-w-0">
                         <input
                             type="file"
                             accept="image/*"
                             @change="handleFileUpload"
                             class="block w-full text-[13px] text-text-sub file:mr-3 file:h-9 file:px-4 file:rounded-full file:border file:border-solid file:border-line-strong file:bg-transparent file:text-[13px] file:font-medium file:text-text-main hover:file:border-text-main file:cursor-pointer"
                         />
                         <p class="mt-2 text-[12px] text-text-sub">PNG、JPG、WEBP，最大 5MB</p>
                     </div>
                 </div>
             </div>

             <label class="block">
                 <span class="label">商品描述</span>
                 <textarea v-model="editingProduct.description" rows="3" class="field"></textarea>
             </label>

             <div class="flex items-center justify-between gap-4 py-1">
                 <div>
                     <p id="recommend-label" class="text-[14px] font-medium">设为店长推荐</p>
                     <p class="text-[12px] text-text-sub">出现在学生端「店长推荐」分类</p>
                 </div>
                 <AppSwitch v-model="editingProduct.is_recommend" label="设为店长推荐" />
             </div>

             <!-- Inventory -->
             <div>
                 <span class="label">库存数量（0 表示售罄）</span>
                 <div class="flex items-center gap-2">
                     <input v-model.number="editingProduct.inventory_count" type="number" min="0" class="field flex-1 tabular-nums" placeholder="999" />
                     <button type="button" @click="editingProduct.inventory_count = 0" class="btn btn-outline btn-sm">设为售罄</button>
                     <button type="button" @click="editingProduct.inventory_count = 999" class="btn btn-outline btn-sm">恢复库存</button>
                 </div>
                 <p class="mt-2 text-[12px] text-text-sub">库存为 0 时商品显示为售罄，学生无法下单。</p>
             </div>
         </div>
         <template #footer>
             <button type="button" @click="showModal = false" class="btn btn-ghost flex-1">取消</button>
             <button type="button" @click="handleSave" class="btn btn-primary flex-1">保存商品</button>
         </template>
     </AppModal>

     <!-- Delete confirmation -->
     <AppModal :open="showDeleteModal" size="sm" title="删除商品" :subtitle="deleteName" @close="showDeleteModal = false">
         <p class="text-[14px] text-text-sub leading-relaxed">商品删除后无法恢复。</p>
         <template #footer>
             <button type="button" @click="showDeleteModal = false" class="btn btn-ghost flex-1">取消</button>
             <button type="button" @click="confirmDelete" class="btn btn-danger flex-1">确认删除</button>
         </template>
     </AppModal>
  </div>
</template>
