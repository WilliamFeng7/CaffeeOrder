
<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useToastStore } from './stores/toast';

const toastStore = useToastStore();
</script>

<template>
  <div id="root" class="bg-background-light overflow-hidden relative">
      <RouterView />
      
      <!-- Global Toast Container -->
      <div class="fixed top-6 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 pointer-events-none w-full max-w-sm px-4">
          <TransitionGroup name="toast">
              <div v-for="toast in toastStore.toasts" :key="toast.id" 
                  class="bg-surface-light/90 backdrop-blur-md shadow-xl border border-white/50 px-4 py-3 rounded-2xl flex items-center gap-3 pointer-events-auto"
                  :class="{
                      'text-green-700 bg-green-50/90 border-green-100': toast.type === 'success',
                      'text-red-700 bg-red-50/90 border-red-100': toast.type === 'error',
                      'text-blue-700 bg-blue-50/90 border-blue-100': toast.type === 'info',
                  }"
              >
                  <span class="material-symbols-rounded text-xl" v-if="toast.type === 'success'">check_circle</span>
                  <span class="material-symbols-rounded text-xl" v-if="toast.type === 'error'">error</span>
                  <span class="material-symbols-rounded text-xl" v-if="toast.type === 'info'">info</span>
                  <span class="text-sm font-bold">{{ toast.message }}</span>
              </div>
          </TransitionGroup>
      </div>
  </div>
</template>

<style>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.9);
}
</style>
