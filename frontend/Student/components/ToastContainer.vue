
<script setup lang="ts">
import { useToastStore } from '../src/stores/toast';
import { storeToRefs } from 'pinia';

const store = useToastStore();
const { toasts } = storeToRefs(store);

const getIcon = (type: string) => {
    switch (type) {
        case 'success': return 'check_circle';
        case 'error': return 'error';
        case 'warning': return 'warning';
        case 'info': return 'info';
        default: return 'info';
    }
};

const getClasses = (type: string) => {
    switch (type) {
        case 'success': return 'bg-green-50 text-green-700 border-green-100';
        case 'error': return 'bg-red-50 text-red-700 border-red-100';
        case 'warning': return 'bg-yellow-50 text-yellow-700 border-yellow-100';
        case 'info': return 'bg-blue-50 text-blue-700 border-blue-100';
        default: return 'bg-white text-gray-700 border-gray-100';
    }
};
</script>

<template>
    <div class="fixed top-4 left-1/2 -translate-x-1/2 z-[99999] flex flex-col gap-2 w-full max-w-sm px-4 pointer-events-none">
        <TransitionGroup name="toast">
            <div 
                v-for="toast in toasts" 
                :key="toast.id"
                class="pointer-events-auto flex items-center p-4 rounded-[20px] shadow-lg border backdrop-blur-sm animate-pop-in"
                :class="getClasses(toast.type)"
            >
                <span class="material-symbols-rounded mr-3 text-xl">{{ getIcon(toast.type) }}</span>
                <span class="font-bold text-sm">{{ toast.message }}</span>
            </div>
        </TransitionGroup>
    </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.9);
}
</style>
