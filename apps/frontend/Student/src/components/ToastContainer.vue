<script setup lang="ts">
/**
 * ToastContainer.vue (Student)
 *
 * The Student app's toast renderer: one ink pill with a small coloured dot
 * for the type (no icon), in keeping with the app's line-only look. It reads
 * the shared toast store, so every existing `useToastStore()` call works.
 * Admin and KDS keep the shared renderer.
 *
 * Motion: drops in on a spring (transitions, so a second toast retargets
 * instead of restarting), the dot pops a beat later, and it leaves upward on
 * the same ease-out it arrived with while the rest glide into place.
 */
import { computed } from 'vue';
import { useToastStore } from '../stores/toast';

const store = useToastStore();
// (Not storeToRefs: the store is defined in packages/shared, whose pinia
// typings are a different copy from this app's.)
const toasts = computed(() => store.toasts);

const DOT: Record<string, string> = {
  success: 'bg-[#7ED6A7]',
  error: 'bg-[#FF9C8F]',
  warning: 'bg-[#F3C77A]',
  info: 'bg-white/55',
};
</script>

<template>
  <!-- Toasts have no controls, so taps go straight through them. -->
  <div
    class="fixed top-[max(env(safe-area-inset-top),16px)] left-1/2 -translate-x-1/2 z-[99999] w-full max-w-sm px-4 pointer-events-none"
    role="region"
    aria-label="Notifications"
  >
    <TransitionGroup name="toast" tag="div" class="relative flex flex-col items-center gap-2">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :aria-live="toast.type === 'error' || toast.type === 'warning' ? 'assertive' : 'polite'"
        role="status"
        class="pointer-events-none flex items-center gap-3 min-h-11 max-w-full pl-4 pr-5 py-2.5 rounded-full bg-[#171C19] text-white shadow-float"
      >
        <span class="size-2 rounded-full shrink-0 pop-in" style="animation-delay: 110ms" :class="DOT[toast.type] ?? DOT.info" aria-hidden="true"></span>
        <span class="text-[14px] font-medium leading-snug">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active {
  transition:
    opacity var(--dur-fade) var(--ease-out),
    transform var(--dur-spring) var(--ease-spring);
}

.toast-move {
  transition: transform var(--dur-spring) var(--ease-spring);
}

.toast-enter-from {
  opacity: 0;
  transform: translate3d(0, -24px, 0) scale(0.94);
}

/* Out the way it came in, taken out of flow so the others glide up. */
.toast-leave-active {
  transition:
    opacity var(--dur-page-out) var(--ease-out),
    transform var(--dur-sheet-out) var(--ease-out);
  position: absolute;
  top: 0;
}

.toast-leave-to {
  opacity: 0;
  transform: translate3d(0, -20px, 0) scale(0.96);
}
</style>
