<script setup lang="ts">
import AppIcon from '@shared/components/AppIcon.vue';
import { ref, onMounted } from 'vue';
import { api } from '../api';
import { useToastStore } from '../stores/toast';

const users = ref<any[]>([]);
const loading = ref(true);
const showModal = ref(false);
const editingUser = ref<any>(null);
const toast = useToastStore();

const fetchUsers = async () => {
    loading.value = true;
    try {
        const data = await api.getUsers();
        // Convert balance from Cents to Yuan for display
        users.value = data.map((u: any) => ({
            ...u,
            balance: u.balance / 100
        }));
    } catch (e: any) {
        console.error(e);
        toast.error('加载用户失败: ' + (e.response?.data?.detail || e.message));
    } finally {
        loading.value = false;
    }
};

const handleEdit = (user: any) => {
    editingUser.value = { ...user }; // Clone
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
        await api.deleteUser(deleteId.value);
        showDeleteModal.value = false;
        fetchUsers();
    }
};



const showDepositModal = ref(false);
const depositAmount = ref(100);
const depositUser = ref<any>(null);

const handleDepositOpen = (user: any) => {
    depositUser.value = user;
    depositAmount.value = 100; 
    showDepositModal.value = true;
};

const handleDepositSubmit = async () => {
    if (depositUser.value && depositAmount.value > 0) {
        // Pass display units (Yuan) - api.deposit() converts to cents exactly once.
        // This used to convert here *and* inside api.deposit(), so a ¥100 top-up
        // was submitted as 1000000 cents (¥10,000).
        try {
            await api.deposit(depositUser.value.id, depositAmount.value);
            showDepositModal.value = false;
            fetchUsers();
            toast.success('充值成功 (Top-up Successful)');
        } catch (e: any) {
            console.error(e);
            toast.error('充值失败: ' + (e.response?.data?.detail || e.message));
        }
    }
};

    const handleSave = async () => {
    if (editingUser.value) {
        // --- Client-Side Validation ---
        const u = editingUser.value;
        const isNew = !u.id;

        // 1. Required Fields
        if (!u.name || !u.username || u.balance === undefined || u.balance === null) {
            toast.warning('姓名、用户名、余额为必填项 (Name, Username, Balance are required)');
            return;
        }

        // 2. Password Validation
        if (isNew && !u.password) {
            toast.warning('新用户必须设置密码 (Password is required for new users)');
            return;
        }
        if (u.password && u.password.length < 8) {
            toast.warning('密码长度必须大于8位 (Password must be > 8 characters)');
            return;
        }

        // 3. Phone Validation
        if (u.phone && u.phone.length !== 11) {
             toast.warning('手机号必须是11位 (Phone number must be 11 digits)');
             return;
        }
        
        try {
            // Balance stays in display units (Yuan) here; api.createUser /
            // api.updateUser each convert to cents once. Spreading `u` is enough.
            const payload = { ...u };

            if (u.id) {
                await api.updateUser(u.id, payload);
            } else {
                await api.createUser(payload);
            }
            showModal.value = false;
            fetchUsers();
            toast.success('保存成功 (Saved Successfully)');
        } catch (e: any) {
            console.error(e);
            let msg = e.response?.data?.detail || e.message;
            if (typeof msg === 'object') {
                msg = JSON.stringify(msg);
            }
            toast.error('保存失败: ' + msg);
        }
    }
};

onMounted(fetchUsers);
</script>

<template>
  <div class="space-y-6 animate-fade-in">
     <div class="flex justify-between items-center">
         <h1 class="text-3xl font-black text-primary tracking-tight">用户管理</h1>
         <button @click="() => { editingUser = { name: '', username: '', password: '', role: 'student', balance: 0 }; showModal = true; }" class="px-6 py-3 bg-[#103E32] text-white rounded-2xl font-bold text-sm shadow-lg shadow-primary/20 hover:scale-105 transition-transform flex items-center gap-2">
             <AppIcon name="user-plus" />
             添加用户
         </button>
     </div>

     <!-- Table Card -->
     <div class="bg-white rounded-[32px] shadow-sm border border-gray-100 overflow-hidden">
        <div class="overflow-x-auto">
            <table class="w-full text-left">
                <thead class="bg-gray-50 border-b border-gray-100">
                    <tr>
                        <th class="px-8 py-5 text-xs font-black text-gray-400 uppercase tracking-widest">用户信息</th>
                        <th class="px-8 py-5 text-xs font-black text-gray-400 uppercase tracking-widest">角色</th>
                        <th class="px-8 py-5 text-xs font-black text-gray-400 uppercase tracking-widest text-right">余额</th>
                        <th class="px-8 py-5 text-xs font-black text-gray-400 uppercase tracking-widest text-right">操作</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-50">
                    <tr v-for="user in users" :key="user.id" class="group hover:bg-gray-50/80 transition-colors">
                        <td class="px-8 py-5">
                            <div class="flex items-center gap-4">
                                <div class="size-10 rounded-full bg-[#103E32]/10 text-[#103E32] flex items-center justify-center font-bold text-sm">
                                    {{ user.username.slice(0,2).toUpperCase() }}
                                </div>
                                <div>
                                    <p class="font-bold text-gray-900">{{ user.name }}</p>
                                    <p class="text-xs text-gray-400 font-mono">{{ user.username }}</p>
                                </div>
                            </div>
                        </td>
                        <td class="px-8 py-5">
                            <span class="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider" 
                                  :class="user.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-green-100 text-green-700'">
                                {{ user.role }}
                            </span>
                        </td>
                        <td class="px-8 py-5 text-right">
                             <p class="font-mono font-bold text-gray-900">¥{{ user.balance.toFixed(2) }}</p>
                        </td>
                        <td class="px-8 py-5 text-right">
                             <!-- Hidden until hover with a mouse; always shown on touch, where hover never happens -->
                             <div v-if="user.role !== 'admin'" class="flex items-center justify-end gap-2 opacity-100 [@media(hover:hover)_and_(pointer:fine)]:opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
                                 <button type="button" @click="handleEdit(user)" aria-label="编辑" class="size-8 [@media(pointer:coarse)]:size-11 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center hover:bg-blue-100 transition-colors">
                                     <AppIcon name="edit" class="text-sm [@media(pointer:coarse)]:text-xl" />
                                 </button>
                                 <button type="button" @click="handleDepositOpen(user)" aria-label="充值" class="size-8 [@media(pointer:coarse)]:size-11 rounded-full bg-green-50 text-green-600 flex items-center justify-center hover:bg-green-100 transition-colors" title="充值">
                                     <AppIcon name="wallet" class="text-sm [@media(pointer:coarse)]:text-xl" />
                                 </button>
                                 <button type="button" @click="handleDelete(user.id)" aria-label="删除" class="size-8 [@media(pointer:coarse)]:size-11 rounded-full bg-red-50 text-red-600 flex items-center justify-center hover:bg-red-100 transition-colors">
                                     <AppIcon name="trash" class="text-sm [@media(pointer:coarse)]:text-xl" />
                                 </button>
                             </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
     </div>

     <!-- Delete Confirmation Modal -->
     <Teleport to="body">
     <div v-if="showDeleteModal" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
         <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showDeleteModal = false"></div>
         <div class="bg-white w-full max-w-sm rounded-[32px] p-8 relative z-10 shadow-2xl animate-scale-in text-center">
             <div class="size-16 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto mb-4">
                 <AppIcon name="trash" class="text-3xl" />
             </div>
             <h3 class="text-xl font-black text-gray-900 mb-2">确认删除?</h3>
             <p class="text-gray-500 text-sm font-bold mb-6">此操作不可逆，用户数据将被永久移除。</p>
             <div class="flex gap-3">
                 <button @click="confirmDelete" class="flex-1 h-12 bg-red-600 hover:bg-red-700 text-white rounded-xl font-bold shadow-lg shadow-red-600/20 transition-colors">确认删除</button>
                 <button @click="showDeleteModal = false" class="flex-1 h-12 bg-gray-100 text-gray-600 rounded-xl font-bold hover:bg-gray-200">取消</button>
             </div>
         </div>
     </div>
     </Teleport>

     <!-- Edit Modal -->
     <Teleport to="body">
     <div v-if="showModal" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
         <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showModal = false"></div>
         <div class="bg-white w-full max-w-lg rounded-[32px] p-8 relative z-10 shadow-2xl animate-scale-in">
             <h3 class="text-2xl font-black text-primary mb-6">{{ editingUser.id ? '编辑用户' : '添加用户' }}</h3>
             <div class="space-y-4">
                 <div>
                     <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">姓名 (Name) <span class="text-red-400">*</span></label>
                     <input v-model="editingUser.name" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20" />
                 </div>
                 <div v-if="!editingUser.id">
                     <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">用户名 (Username) <span class="text-red-400">*</span></label>
                     <input v-model="editingUser.username" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20" />
                 </div>
                 <div>
                     <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">密码 (Password)</label>
                     <input v-model="editingUser.password" type="password" autocomplete="new-password" placeholder="留空则不修改 (Leave empty to keep)" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20" />
                     <p v-if="!editingUser.id" class="text-[10px] text-red-400 font-bold mt-1 ml-2">* 必填 (Required, >8 chars)</p>
                     <p v-else class="text-[10px] text-gray-400 font-bold mt-1 ml-2">若修改需 >8 位 (If changed, must be >8 chars)</p>
                 </div>
                 <div>
                     <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">余额 (¥) <span class="text-red-400">*</span></label>
                     <input v-model.number="editingUser.balance" type="number" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20" />
                 </div>
                 <div>
                     <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">角色 <span class="text-red-400">*</span></label>
                     <select v-model="editingUser.role" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20">
                         <option value="student">学生</option>
                         <option value="admin">管理员</option>
                     </select>
                 </div>
                 <div>
                     <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">手机号 (Phone) <span class="text-gray-300 font-normal">- Optional</span></label>
                     <input v-model="editingUser.phone" placeholder="11位数字 (11 digits)" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20" />
                 </div>
                 <div>
                     <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">邮箱 (Email) <span class="text-gray-300 font-normal">- Optional</span></label>
                     <input v-model="editingUser.email" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20" />
                 </div>
                 
                 <div class="pt-4 flex gap-3">
                     <button @click="handleSave" class="flex-1 h-14 bg-primary text-white rounded-xl font-bold shadow-lg shadow-primary/20">保存更改</button>
                     <button @click="showModal = false" class="flex-1 h-14 bg-gray-100 text-gray-600 rounded-xl font-bold hover:bg-gray-200">取消</button>
                 </div>
             </div>
         </div>
     </div>
     </Teleport>

     <!-- Deposit Modal -->
     <Teleport to="body">
     <div v-if="showDepositModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
         <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showDepositModal = false"></div>
         <div class="bg-white w-full max-w-sm rounded-[32px] p-8 relative z-10 shadow-2xl animate-scale-in">
             <div class="mb-6 flex flex-col items-center">
                 <div class="size-16 rounded-full bg-green-50 text-green-600 flex items-center justify-center mb-4">
                     <AppIcon name="card" class="text-3xl" />
                 </div>
                 <h3 class="text-xl font-black text-primary">账户充值 (Top Up)</h3>
                 <p class="text-gray-400 text-sm font-bold mt-1">为 {{ depositUser?.name }} 充值</p>
             </div>
             
             <div class="space-y-4">
                 <div class="grid grid-cols-3 gap-2">
                     <button @click="depositAmount = 50" :class="depositAmount === 50 ? 'bg-primary text-white' : 'bg-gray-50 text-gray-600'" class="h-10 rounded-xl font-bold text-sm transition-colors">¥50</button>
                     <button @click="depositAmount = 100" :class="depositAmount === 100 ? 'bg-primary text-white' : 'bg-gray-50 text-gray-600'" class="h-10 rounded-xl font-bold text-sm transition-colors">¥100</button>
                     <button @click="depositAmount = 200" :class="depositAmount === 200 ? 'bg-primary text-white' : 'bg-gray-50 text-gray-600'" class="h-10 rounded-xl font-bold text-sm transition-colors">¥200</button>
                 </div>
                 
                 <div>
                     <label class="block text-xs font-black text-gray-400 uppercase tracking-widest mb-1 ml-2">充值金额 (¥)</label>
                     <input v-model.number="depositAmount" type="number" class="w-full h-12 bg-gray-50 rounded-xl px-4 font-bold outline-none focus:ring-2 focus:ring-primary/20 text-center text-lg" />
                 </div>
                 
                 <div class="pt-2 flex gap-3">
                     <button @click="handleDepositSubmit" class="flex-1 h-12 bg-green-600 hover:bg-green-700 text-white rounded-xl font-bold shadow-lg shadow-green-600/20 transition-colors">确认充值</button>
                     <button @click="showDepositModal = false" class="flex-1 h-12 bg-gray-100 text-gray-600 rounded-xl font-bold hover:bg-gray-200">取消</button>
                 </div>
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
