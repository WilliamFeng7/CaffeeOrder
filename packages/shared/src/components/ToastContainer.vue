<script setup lang="ts">
/**
 * Shared toast renderer for Student / Admin / Barista.
 *
 * One quiet ink pill at the top of the screen; the type is carried by a small
 * coloured glyph, not by a coloured box. Toasts drop in on a spring and leave
 * upwards; the others glide to close the gap.
 *
 * Accessibility: the live region is what the earlier copies lacked - a toast is
 * the only feedback for "order placed" / "wrong password", and without
 * `aria-live` a screen-reader user never heard it.
 */
import AppIcon from './AppIcon.vue';
import type { IconName } from '../icons';
import { useToastStore } from '../toast';
import { storeToRefs } from 'pinia';

const store = useToastStore();
const { toasts } = storeToRefs(store);

const GLYPH: Record<string, { icon: IconName; color: string }> = {
  success: { icon: 'check-circle', color: 'text-[#7ED6A7]' },
  error: { icon: 'warning-circle', color: 'text-[#FF9C8F]' },
  warning: { icon: 'warning', color: 'text-[#F3C77A]' },
  info: { icon: 'info', color: 'text-white/60' },
};
const glyph = (type: string) => GLYPH[type] ?? GLYPH.info;
</script>

<template>
  <!-- Toasts have no controls, so taps go straight through them: a toast over
       a header used to swallow the back button and the sheet's drag handle. -->
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
        class="pointer-events-none flex items-center gap-2.5 min-h-11 max-w-full pl-3.5 pr-5 py-2.5 rounded-full bg-[#171C19] text-white shadow-float"
      >
        <AppIcon :name="glyph(toast.type).icon" class="text-lg shrink-0" :class="glyph(toast.type).color" />
        <span class="text-[14px] font-medium leading-snug">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
/* In on a spring from just above (transitions, not keyframes, so a toast
   raised twice in a row retargets instead of restarting); out upwards in
   ~65% of the time, taken out of flow so the rest glide up. */
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

.toast-leave-active {
  transition:
    opacity var(--dur-page-out) var(--ease-out),
    transform var(--dur-sheet-out) var(--ease-out);
  position: absolute;
  top: 0;
}

.toast-leave-to {
  opacity: 0;
  transform: translate3d(0, -16px, 0) scale(0.96);
}
</style>
