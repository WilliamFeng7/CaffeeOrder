<script setup lang="ts">
import AppIcon from '@shared/components/AppIcon.vue';
import AppModal from '@shared/components/AppModal.vue';
import { ref, computed, onMounted } from 'vue';
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

const deleteName = computed(() => {
    const u = users.value.find(x => x.id === deleteId.value);
    return u ? (u.name || u.username) : '';
});

const initials = (user: any) => String(user.name || user.username || '?').slice(0, 2).toUpperCase();

const openCreate = () => {
    editingUser.value = { name: '', username: '', password: '', role: 'student', balance: 0 };
    showModal.value = true;
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
  <div class="space-y-6">
     <div class="flex flex-wrap items-end justify-between gap-4 animate-slide-up-content">
         <div>
             <p class="eyebrow">{{ users.length }} 位用户</p>
             <h1 class="mt-2 font-serif text-[34px] font-medium leading-tight tracking-[-0.015em]">用户管理</h1>
         </div>
         <button type="button" @click="openCreate" class="btn btn-primary btn-sm">
             <AppIcon name="plus" class="text-base" />
             添加用户
         </button>
     </div>

     <!-- Table -->
     <div class="card overflow-hidden animate-slide-up-content" style="animation-delay: 60ms">
        <div class="overflow-x-auto quiet-scrollbar">
            <table class="w-full text-left">
                <thead>
                    <tr class="border-b border-line">
                        <th class="px-6 py-3.5 eyebrow font-medium">用户</th>
                        <th class="px-6 py-3.5 eyebrow font-medium">角色</th>
                        <th class="px-6 py-3.5 eyebrow font-medium text-right">余额</th>
                        <th class="px-6 py-3.5 eyebrow font-medium text-right">操作</th>
                    </tr>
                </thead>
                <tbody v-if="loading && !users.length">
                    <tr v-for="i in 5" :key="i" class="border-b border-line last:border-0">
                        <td colspan="4" class="px-6 py-4">
                            <div class="h-9 rounded-tile bg-cream animate-pulse"></div>
                        </td>
                    </tr>
                </tbody>
                <tbody v-else class="stagger-in">
                    <tr v-for="user in users" :key="user.id" class="group border-b border-line last:border-0 hover:bg-background-light transition-colors duration-color">
                        <td class="px-6 py-4">
                            <div class="flex items-center gap-3.5">
                                <span class="size-9 rounded-full bg-cream text-text-main flex items-center justify-center text-[12px] font-medium shrink-0">
                                    {{ initials(user) }}
                                </span>
                                <div class="min-w-0">
                                    <p class="text-[14px] font-medium truncate">{{ user.name }}</p>
                                    <p class="text-[12px] text-text-sub font-mono truncate">{{ user.username }}</p>
                                </div>
                            </div>
                        </td>
                        <td class="px-6 py-4">
                            <span class="chip" :class="user.role === 'admin' ? 'chip-warm' : user.role === 'barista' ? 'chip-accent' : 'chip-quiet'">{{ user.role }}</span>
                        </td>
                        <td class="px-6 py-4 text-right">
                             <span class="font-serif text-[16px] font-medium tabular-nums">¥{{ user.balance.toFixed(2) }}</span>
                        </td>
                        <td class="px-6 py-4 text-right">
                             <!-- Hidden until hover with a mouse; always shown on touch, where hover never happens -->
                             <div v-if="user.role !== 'admin'" class="flex items-center justify-end gap-1 opacity-100 [@media(hover:hover)_and_(pointer:fine)]:opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity duration-color">
                                 <button type="button" @click="handleEdit(user)" aria-label="编辑" title="编辑" class="icon-btn size-8 [@media(pointer:coarse)]:size-11">
                                     <AppIcon name="edit" weight="light" class="text-[18px]" />
                                 </button>
                                 <button type="button" @click="handleDepositOpen(user)" aria-label="充值" title="充值" class="icon-btn size-8 [@media(pointer:coarse)]:size-11">
                                     <AppIcon name="wallet" weight="light" class="text-[18px]" />
                                 </button>
                                 <button type="button" @click="handleDelete(user.id)" aria-label="删除" title="删除" class="icon-btn size-8 [@media(pointer:coarse)]:size-11 hover:!text-danger hover:!bg-danger-soft">
                                     <AppIcon name="trash" weight="light" class="text-[18px]" />
                                 </button>
                             </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
     </div>

     <!-- Delete confirmation -->
     <AppModal :open="showDeleteModal" size="sm" title="删除用户" :subtitle="deleteName" @close="showDeleteModal = false">
         <p class="text-[14px] text-text-sub leading-relaxed">此操作不可撤销，该用户的数据将被永久移除。</p>
         <template #footer>
             <button type="button" @click="showDeleteModal = false" class="btn btn-ghost flex-1">取消</button>
             <button type="button" @click="confirmDelete" class="btn btn-danger flex-1">确认删除</button>
         </template>
     </AppModal>

     <!-- Edit / create -->
     <AppModal :open="showModal" :title="editingUser?.id ? '编辑用户' : '添加用户'" @close="showModal = false">
         <div v-if="editingUser" class="space-y-4">
             <label class="block">
                 <span class="label">姓名 <span class="text-danger">*</span></span>
                 <input v-model="editingUser.name" class="field" />
             </label>
             <label v-if="!editingUser.id" class="block">
                 <span class="label">用户名 <span class="text-danger">*</span></span>
                 <input v-model="editingUser.username" class="field" autocomplete="off" />
             </label>
             <label class="block">
                 <span class="label">密码</span>
                 <input v-model="editingUser.password" type="password" autocomplete="new-password" :placeholder="editingUser.id ? '留空则不修改' : '至少 8 位'" class="field" />
                 <span class="mt-1.5 block text-[12px]" :class="editingUser.id ? 'text-text-sub' : 'text-danger'">
                     {{ editingUser.id ? '若修改需大于 8 位' : '必填，大于 8 位' }}
                 </span>
             </label>
             <div class="grid grid-cols-2 gap-4">
                 <label class="block">
                     <span class="label">余额 (¥) <span class="text-danger">*</span></span>
                     <input v-model.number="editingUser.balance" type="number" class="field tabular-nums" />
                 </label>
                 <label class="block">
                     <span class="label">角色 <span class="text-danger">*</span></span>
                     <select v-model="editingUser.role" class="field">
                         <option value="student">学生</option>
                         <option value="admin">管理员</option>
                     </select>
                 </label>
             </div>
             <div class="grid grid-cols-2 gap-4">
                 <label class="block">
                     <span class="label">手机号 <span class="text-text-sub/70">选填</span></span>
                     <input v-model="editingUser.phone" placeholder="11 位数字" inputmode="numeric" class="field tabular-nums" />
                 </label>
                 <label class="block">
                     <span class="label">邮箱 <span class="text-text-sub/70">选填</span></span>
                     <input v-model="editingUser.email" type="email" class="field" />
                 </label>
             </div>
         </div>
         <template #footer>
             <button type="button" @click="showModal = false" class="btn btn-ghost flex-1">取消</button>
             <button type="button" @click="handleSave" class="btn btn-primary flex-1">保存</button>
         </template>
     </AppModal>

     <!-- Top up -->
     <AppModal :open="showDepositModal" size="sm" title="账户充值" :subtitle="depositUser ? `为 ${depositUser.name || depositUser.username} 充值` : ''" @close="showDepositModal = false">
         <div class="grid grid-cols-3 gap-2">
             <button
                 v-for="amount in [50, 100, 200]"
                 :key="amount"
                 type="button"
                 @click="depositAmount = amount"
                 class="h-11 rounded-full border text-[14px] font-medium tabular-nums transition-colors duration-color"
                 :class="depositAmount === amount ? 'bg-text-main border-text-main text-white' : 'border-line text-text-main hover:border-text-main'"
             >¥{{ amount }}</button>
         </div>
         <label class="block mt-5">
             <span class="label">充值金额 (¥)</span>
             <input v-model.number="depositAmount" type="number" class="field text-center font-serif !text-[22px] tabular-nums" />
         </label>
         <template #footer>
             <button type="button" @click="showDepositModal = false" class="btn btn-ghost flex-1">取消</button>
             <button type="button" @click="handleDepositSubmit" class="btn btn-primary flex-1">确认充值</button>
         </template>
     </AppModal>
  </div>
</template>
