<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

const menuItems = [
    { name: '经营概览', path: '/', icon: 'dashboard' },
    { name: '用户与账户', path: '/users', icon: 'group' },
    { name: '业务订单', path: '/orders', icon: 'shopping_cart' },
    { name: '商品管理', path: '/products', icon: 'inventory_2' },
    
    { name: '财务与结算', path: '/finance', icon: 'monitoring' },
    { name: '系统设置', path: '/settings', icon: 'settings' },
];

const handleLogout = () => {
    sessionStorage.removeItem('admin_token');
    router.push('/login');
};
</script>

<template>
  <div class="flex h-screen bg-gray-50 font-sans text-gray-900 overflow-hidden text-sm lg:text-base">
    <!-- Sidebar -->
    <aside class="w-20 md:w-72 bg-[#103E32] text-white flex flex-col shadow-xl z-50">
        <div class="p-4 md:p-8 pb-4">
            <h1 class="text-xl md:text-2xl font-black tracking-tight flex items-center gap-3">
                <span class="material-symbols-rounded text-[#DCCA98]">coffee</span>
                <span class="hidden md:inline">OTIA 咖啡后台</span>
            </h1>
            <p class="hidden md:block text-xs text-white/40 mt-1 uppercase tracking-widest font-bold">管理系统</p>
        </div>

        <nav class="flex-1 px-2 md:px-4 py-6 space-y-2">
            <router-link 
                v-for="item in menuItems" 
                :key="item.path" 
                :to="item.path"
                class="flex items-center justify-center md:justify-start gap-4 px-3 md:px-6 py-4 rounded-xl md:rounded-2xl transition-all duration-300 group"
                :class="route.path === item.path ? 'bg-[#DCCA98] text-[#103E32] shadow-lg shadow-[#DCCA98]/20 translate-x-1 md:translate-x-2' : 'hover:bg-white/5 text-white/70 hover:text-white'"
            >
                <span class="material-symbols-rounded text-2xl group-hover:scale-110 transition-transform">{{ item.icon }}</span>
                <span class="hidden md:block font-bold text-sm tracking-wide">{{ item.name }}</span>
            </router-link>
        </nav>

        <div class="p-4 md:p-6 border-t border-white/10">
            <button 
                @click="handleLogout"
                class="w-full flex items-center justify-center gap-3 px-3 md:px-6 py-4 rounded-xl md:rounded-2xl bg-white/5 hover:bg-red-500/20 hover:text-red-200 transition-all duration-300 text-sm font-bold tracking-wide"
            >
                <span class="material-symbols-rounded">logout</span>
                <span class="hidden md:block">退出登录</span>
            </button>
        </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col min-w-0 relative">
        <!-- Header -->
        <header class="h-20 bg-white/80 backdrop-blur-md border-b border-gray-100 flex items-center justify-between px-8 shadow-sm z-40 sticky top-0">
            <h2 class="text-xl font-black text-[#103E32]">{{ menuItems.find(i => i.path === route.path)?.name || '概览' }}</h2>
            <div class="flex items-center gap-4">
                <div class="flex flex-col items-end mr-2">
                    <span class="text-xs font-black text-gray-400 uppercase tracking-widest">Administrator</span>
                    <span class="text-sm font-bold text-gray-900">Admin User</span>
                </div>
                <div class="size-11 rounded-2xl bg-[#DCCA98] flex items-center justify-center text-[#103E32] font-black shadow-md">
                    AD
                </div>
            </div>
        </header>

        <!-- Content Area -->
        <div class="flex-1 overflow-auto p-4 md:p-8 bg-gray-50/50 scroll-smooth relative">
            <router-view :key="route.fullPath" />
        </div>
    </main>
  </div>
</template>
