<script setup lang="ts">
/**
 * AdminLayout.vue
 *
 * Console frame: a light sidebar whose white highlight springs to the current
 * section, a slim header, and the page area. Pages swap with the shared
 * "page" transition (old page fades quickly, new one rises into place).
 */
import AppIcon from '@shared/components/AppIcon.vue';
import { computed, ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { auth } from '@shared/auth';
import type { IconName } from '@shared/icons';

const router = useRouter();
const route = useRoute();

const menuItems: { name: string; path: string; icon: IconName }[] = [
    { name: '经营概览', path: '/', icon: 'grid' },
    { name: '用户与账户', path: '/users', icon: 'users' },
    { name: '业务订单', path: '/orders', icon: 'receipt' },
    { name: '商品管理', path: '/products', icon: 'package' },
    { name: '财务与结算', path: '/finance', icon: 'chart' },
    { name: '系统设置', path: '/settings', icon: 'gear' },
];

// Each nav row is 44px tall with 4px between rows.
const NAV_STEP = 48;
const activeIndex = computed(() => menuItems.findIndex(i => i.path === route.path));
const section = computed(() => menuItems[activeIndex.value]?.name ?? '概览');

const today = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' });

// A new page starts at the top, not at the previous page's scroll offset.
const scroller = ref<HTMLElement | null>(null);
const resetScroll = () => {
    if (scroller.value) scroller.value.scrollTop = 0;
};

const handleLogout = () => {
    auth.clearToken();
    router.push('/login');
};
</script>

<template>
  <div class="flex h-screen bg-background-light font-sans text-text-main overflow-hidden text-[14px]">
    <!-- Sidebar -->
    <aside class="w-[72px] lg:w-60 shrink-0 border-r border-line flex flex-col z-20">
        <div class="h-20 flex items-center justify-center lg:justify-start gap-2 lg:px-7">
            <span class="font-serif text-[22px] font-semibold tracking-tight">OTIA</span>
            <span class="hidden lg:inline eyebrow mt-1">Admin</span>
        </div>

        <nav class="relative flex-1 px-3 pt-2" aria-label="主导航">
            <span
                v-show="activeIndex >= 0"
                class="absolute left-3 right-3 top-2 h-11 rounded-tile bg-surface-light border border-line transition-transform duration-spring ease-spring pointer-events-none"
                :style="{ transform: `translate3d(0, ${Math.max(0, activeIndex) * NAV_STEP}px, 0)` }"
                aria-hidden="true"
            ></span>
            <router-link
                v-for="(item, i) in menuItems"
                :key="item.path"
                :to="item.path"
                :title="item.name"
                class="relative z-10 h-11 mb-1 flex items-center justify-center lg:justify-start gap-3 px-3.5 rounded-tile transition-colors duration-color"
                :class="i === activeIndex ? 'text-text-main font-medium' : 'text-text-sub hover:text-text-main'"
            >
                <AppIcon :name="item.icon" :weight="i === activeIndex ? 'regular' : 'light'" class="text-[20px]" />
                <span class="hidden lg:inline">{{ item.name }}</span>
            </router-link>
        </nav>

        <div class="p-3 border-t border-line">
            <button
                type="button"
                @click="handleLogout"
                title="退出登录"
                class="w-full h-11 flex items-center justify-center lg:justify-start gap-3 px-3.5 rounded-tile text-text-sub hover:text-danger hover:bg-danger-soft"
            >
                <AppIcon name="sign-out" weight="light" class="text-[20px]" />
                <span class="hidden lg:inline">退出登录</span>
            </button>
        </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col min-w-0 relative">
        <header class="h-20 shrink-0 flex items-center justify-between gap-6 px-6 lg:px-10 border-b border-line">
            <p class="text-[13px] text-text-sub">
                管理后台
                <span class="mx-2 text-line-strong">/</span>
                <span class="text-text-main font-medium">{{ section }}</span>
            </p>
            <div class="flex items-center gap-4">
                <span class="hidden md:inline text-[13px] text-text-sub">{{ today }}</span>
                <span class="size-9 rounded-full border border-line flex items-center justify-center text-[12px] font-medium" title="Administrator">AD</span>
            </div>
        </header>

        <div ref="scroller" class="flex-1 overflow-auto quiet-scrollbar px-6 lg:px-10 pt-8 pb-12 relative">
            <router-view v-slot="{ Component }">
                <Transition name="page" mode="out-in" @before-enter="resetScroll">
                    <component :is="Component" :key="route.fullPath" />
                </Transition>
            </router-view>
        </div>
    </main>
  </div>
</template>
