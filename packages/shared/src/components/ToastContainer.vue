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
import AppIcon from './AppIcon.vue';
import type { IconName } from '../icons';
import { useToastStore } from '../toast';
import { storeToRefs } from 'pinia';

const store = useToastStore();
const { toasts } = storeToRefs(store);

const getIcon = (type: string): IconName => {
  switch (type) {
    case 'success': return 'check-circle';
    case 'error': return 'warning-circle';
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
  <!-- Toasts have no controls, so taps go straight through them: a toast over
       a header used to swallow the back button and the sheet's drag handle. -->
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
        class="pointer-events-none flex items-center gap-3 px-4 py-3.5 rounded-2xl shadow-lg border"
        :class="getClasses(toast.type)"
      >
        <AppIcon :name="getIcon(toast.type)" weight="fill" class="text-xl" />
        <span class="font-semibold text-[15px]">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
/* Toasts arrive with the same gliding ease-out as other entrances and leave in
   ~65% of the time; transitions (not keyframes) so a toast raised twice in a
   row retargets instead of restarting. */
.toast-enter-active {
  transition: opacity var(--dur-fade) var(--ease-out),
              transform var(--dur-enter) var(--ease-out);
}

.toast-move {
  transition: transform var(--dur-enter) var(--ease-out);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-16px) scale(0.98);
}

/* Take the departing toast out of flow so the others slide up smoothly. */
.toast-leave-active {
  transition: opacity var(--dur-sheet-out) var(--ease-out),
              transform var(--dur-sheet-out) var(--ease-out);
  position: absolute;
  width: 100%;
}
</style>
