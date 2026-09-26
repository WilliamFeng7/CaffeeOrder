<script setup lang="ts">
/**
 * Shared toast renderer for Student / Admin / Barista.
 *
 * Three near-identical implementations used to exist: a `ToastContainer.vue`
 * copy in Student and Admin, plus a third inline variant inside Barista's
 * App.vue and a fourth inline pill inside Student's StudentLayout. All of them
 * read the same store, so migrating the store alone would have made every toast
 * render twice in the Student app. This is the single renderer.
 *
 * Accessibility: the live region is what the previous copies lacked - a toast is
 * the only feedback for "order placed" / "wrong password", and without
 * `aria-live` a screen-reader user never heard it.
 */
import { useToastStore } from '../toast';
import { storeToRefs } from 'pinia';

const store = useToastStore();
const { toasts } = storeToRefs(store);

const getIcon = (type: string) => {
  switch (type) {
    case 'success': return 'check_circle';
    case 'error': return 'error';
    case 'warning': return 'warning';
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
  <div
    class="fixed top-4 left-1/2 -translate-x-1/2 z-[99999] flex flex-col gap-2 w-full max-w-sm px-4 pointer-events-none"
    role="region"
    aria-label="Notifications"
  >
    <TransitionGroup name="toast" tag="div" class="flex flex-col gap-2">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :aria-live="toast.type === 'error' || toast.type === 'warning' ? 'assertive' : 'polite'"
        role="status"
        class="pointer-events-auto flex items-center p-4 rounded-[20px] shadow-lg border backdrop-blur-sm"
        :class="getClasses(toast.type)"
      >
        <span class="material-symbols-rounded mr-3 text-xl" aria-hidden="true">{{ getIcon(toast.type) }}</span>
        <span class="font-bold text-sm">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.3s cubic-bezier(0.23, 1, 0.32, 1),
              transform 0.3s cubic-bezier(0.23, 1, 0.32, 1);
}

.toast-move {
  transition: transform 0.3s cubic-bezier(0.23, 1, 0.32, 1);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.96);
}

/* Take the departing toast out of flow so the others slide up smoothly;
   leaving is quicker than arriving. */
.toast-leave-active {
  transition-duration: 0.2s;
  position: absolute;
  width: 100%;
}
</style>
