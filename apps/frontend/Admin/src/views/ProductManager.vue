<script setup lang="ts">
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

onMounted(fetchProducts);
</script>

<template>
  <div class="space-y-6 animate-fade-in">
     <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
         <h1 class="text-3xl font-black text-primary tracking-tight">商品管理</h1>
         
         <div class="flex gap-4 w-full md:w-auto">
             <div class="relative flex-1 md:w-64">
                 <span class="material-symbols-rounded absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">search</span>
                 <input 
                    v-model="searchQuery" 
                    type="text" 
                    placeholder="搜索商品..." 
                    class="w-full h-12 pl-12 pr-4 bg-white border border-gray-100 rounded-2xl font-bold text-sm outline-none focus:ring-2 focus:ring-primary/20 shadow-sm"
                 />
             </div>
             
             <button @click="handleCreate" class="px-6 h-12 bg-[#103E32] text-white rounded-2xl font-bold text-sm shadow-lg shadow-primary/20 hover:scale-105 transition-transform flex items-center gap-2 shrink-0">
                 <span class="material-symbols-rounded">add_circle</span>
                 添加商品
             </button>
         </div>
     </div>

     <!-- Grid Layout for Products -->
     <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
         <div v-for="prod in filteredProducts" :key="prod.id" class="bg-white p-5 rounded-[32px] border border-gray-100 shadow-sm flex gap-4 group hover:shadow-md transition-all duration-300 relative" :class="{ 'opacity-60': prod.inventory_count <= 0 }">
             <!-- Sold Out Badge -->
             <div v-if="prod.inventory_count <= 0" class="absolute -top-2 -right-2 bg-red-500 text-white text-[10px] font-black px-3 py-1 rounded-full shadow-lg z-10">售罄</div>
             
             <!-- Image -->
             <div class="size-24 rounded-2xl bg-gray-100 bg-cover bg-center shrink-0" :class="{ 'grayscale': prod.inventory_count <= 0 }" :style="{ backgroundImage: `url(${prod.image || '/coffee-cup.png'})` }"></div>
             
             <div class="flex-1 min-w-0 flex flex-col justify-between py-1">
                 <div>
                     <div class="flex justify-between items-start gap-2">
                         <h3 class="font-bold text-gray-900 truncate">{{ prod.name }}</h3>
                         <div class="flex gap-1 shrink-0">
                             <span v-if="prod.inventory_count <= 0" class="px-2 py-0.5 bg-red-100 text-red-600 rounded-md text-[10px] font-black">售罄</span>
                             <span class="px-2 py-0.5 bg-orange-100 text-orange-700 rounded-md text-[10px] font-black uppercase">{{ prod.category }}</span>
                         </div>
                     </div>
                     <p class="text-xs text-gray-400 mt-1 line-clamp-2">{{ prod.description }}</p>
                 </div>
                 
                 <div class="flex justify-between items-end mt-2">
                     <div class="flex items-baseline gap-2">
                         <span class="font-black text-xl text-primary">¥{{ prod.price.toFixed(2) }}</span>
                         <span class="text-[10px] font-bold text-gray-400">库存: {{ prod.inventory_count }}</span>
                     </div>
                     
                     <!-- Hidden until hover with a mouse; always shown on touch, where hover never happens -->
                     <div class="flex gap-2 opacity-100 [@media(hover:hover)_and_(pointer:fine)]:opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
                         <button type="button" @click="handleEdit(prod)" aria-label="编辑" class="size-8 [@media(pointer:coarse)]:size-11 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center hover:bg-blue-100">
                             <span class="material-symbols-rounded text-sm [@media(pointer:coarse)]:text-xl" aria-hidden="true">edit</span>
                         </button>
                         <button type="button" @click="handleDelete(prod.id)" aria-label="删除" class="size-8 [@media(pointer:coarse)]:size-11 rounded-full bg-red-50 text-red-600 flex items-center justify-center hover:bg-red-100">
                             <span class="material-symbols-rounded text-sm [@media(pointer:coarse)]:text-xl" aria-hidden="true">delete</span>
                         </button>
                     </div>
                 </div>
             </div>
         </div>
     </div>
     
     <div v-if="filteredProducts.length === 0 && !loading" class="text-center py-20 text-gray-400">
         <p class="font-bold">暂无商品</p>
     </div>

     <!-- Modal -->
     <Teleport to="body">
     <div v-if="showModal" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
         <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showModal = false"></div>
         <div class="bg-white w-full max-w-lg rounded-[32px] p-8 relative z-10 shadow-2xl animate-scale-in max-h-[85vh] overflow-y-auto">
             <h3 class="text-2xl font-black text-primary mb-6">{{ editingProduct.id ? '编辑商品' : '添加商品' }}</h3>
             
             <div class="space-y-4">
                 <div>
                     <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">商品名称</label>
                     <input v-model="editingProduct.name" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20" placeholder="例如：拿铁" />
                 </div>
                                  <div class="grid grid-cols-2 gap-4">
                      <div>
                          <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">价格 (¥)</label>
                          <input v-model.number="editingProduct.price" type="number" step="0.5" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20" />
                      </div>
                      <div>
                          <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">分类</label>
                          <select v-model="editingProduct.category" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20">
                              <option value="seasonal">当季特供 (Seasonal)</option>
                              <option value="coffee">咖啡 (Coffee)</option>
                              <option value="fruit">果茶 (Fruit Tea)</option>
                              <option value="bakery">烘焙 (Bakery)</option>
                          </select>
                      </div>
                  </div>

                  <div>
                      <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">商品图片</label>
                      <div class="flex gap-4 items-center">
                           <div class="size-20 rounded-2xl bg-gray-100 bg-cover bg-center shrink-0 border border-gray-200" 
                                :style="{ backgroundImage: `url(${editingProduct.image || '/coffee-cup.png'})` }">
                           </div>
                           <div class="flex-1">
                               <input 
                                   type="file" 
                                   accept="image/*"
                                   @change="handleFileUpload"
                                   class="block w-full text-sm text-gray-500
                                          file:mr-4 file:py-2 file:px-4
                                          file:rounded-full file:border-0
                                          file:text-xs file:font-semibold
                                          file:bg-primary/10 file:text-primary
                                          hover:file:bg-primary/20
                                   "
                               />
                               <p class="text-[10px] text-gray-400 mt-2">支持 PNG, JPG, WEBP. (Max 5MB)</p>
                           </div>
                      </div>
                  </div>

                  <div>
                      <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">商品描述</label>
                      <textarea v-model="editingProduct.description" class="w-full h-24 bg-gray-50 rounded-xl p-4 font-medium outline-none focus:ring-2 focus:ring-primary/20 resize-none"></textarea>
                  </div>

                  <div class="flex items-center gap-3 bg-yellow-50 p-4 rounded-xl border border-yellow-100 cursor-pointer" @click="editingProduct.is_recommend = !editingProduct.is_recommend">
                      <div class="size-6 rounded-full border-2 flex items-center justify-center transition-colors"
                           :class="editingProduct.is_recommend ? 'bg-yellow-500 border-yellow-500' : 'border-gray-300 bg-white'">
                          <span v-if="editingProduct.is_recommend" class="material-symbols-rounded text-white text-sm">check</span>
                      </div>
                       <span class="font-bold text-gray-700 text-sm">设为店长推荐 (Store Manager Recommend)</span>
                   </div>

                   <!-- Inventory Control -->
                   <div>
                       <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">库存数量 (设为 0 表示售罄)</label>
                       <div class="flex items-center gap-4">
                           <input v-model.number="editingProduct.inventory_count" type="number" min="0" 
                               class="flex-1 h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20" 
                               placeholder="999" />
                           <button type="button" @click="editingProduct.inventory_count = 0" 
                               class="h-12 px-4 bg-red-50 text-red-600 rounded-xl font-bold text-sm hover:bg-red-100 transition-colors flex items-center gap-2">
                               <span class="material-symbols-rounded text-lg">block</span>
                               设为售罄
                           </button>
                           <button type="button" @click="editingProduct.inventory_count = 999" 
                               class="h-12 px-4 bg-green-50 text-green-600 rounded-xl font-bold text-sm hover:bg-green-100 transition-colors flex items-center gap-2">
                               <span class="material-symbols-rounded text-lg">inventory_2</span>
                               恢复库存
                           </button>
                       </div>
                       <p class="text-[10px] text-gray-400 mt-2 ml-2">提示: 库存为 0 时商品将显示为售罄状态，学生无法下单购买</p>
                   </div>
                 
                 <div class="pt-4 flex gap-3">
                     <button @click="handleSave" class="flex-1 h-14 bg-primary text-white rounded-xl font-bold shadow-lg shadow-primary/20 hover:scale-[1.02] transition-transform">保存商品</button>
                     <button @click="showModal = false" class="flex-1 h-14 bg-gray-100 text-gray-600 rounded-xl font-bold hover:bg-gray-200">取消</button>
                 </div>
             </div>
         </div>
     </div>
     </Teleport>

     <!-- Delete Component -->
     <Teleport to="body">
     <div v-if="showDeleteModal" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
         <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showDeleteModal = false"></div>
         <div class="bg-white w-full max-w-sm rounded-[32px] p-8 relative z-10 shadow-2xl animate-scale-in text-center">
             <div class="size-16 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto mb-4">
                 <span class="material-symbols-rounded text-3xl">delete_forever</span>
             </div>
             <h3 class="text-xl font-black text-gray-900 mb-2">确认删除?</h3>
             <p class="text-gray-500 text-sm font-bold mb-6">商品删除后无法恢复。</p>
             <div class="flex gap-3">
                 <button @click="confirmDelete" class="flex-1 h-12 bg-red-600 hover:bg-red-700 text-white rounded-xl font-bold shadow-lg shadow-red-600/20 transition-colors">确认删除</button>
                 <button @click="showDeleteModal = false" class="flex-1 h-12 bg-gray-100 text-gray-600 rounded-xl font-bold hover:bg-gray-200">取消</button>
             </div>
         </div>
     </div>
     </Teleport>
  </div>
</template>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.4s ease-out forwards;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-scale-in {
    animation: scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}
</style>
