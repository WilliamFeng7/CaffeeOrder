<script setup lang="ts">
/**
 * BottomSheet.vue
 *
 * 短表单面板 (edit profile, change password). A bottom sheet on phones and a
 * centred card on iPad. It rises in on the drawer curve and leaves the same
 * way, a little faster (the old v-if panels vanished on close); drag the header
 * down to close. While the on-screen keyboard is up, the sheet moves above it
 * so the field being typed into stays visible.
 */
import { ref, toRef, watch, nextTick } from 'vue';
import { useSheetDrag } from '../composables/useSheetDrag';
import { useKeyboardInset } from '../composables/useKeyboardInset';
import { motionMs } from '@shared/motion';

const props = defineProps<{
  open: boolean;
  title: string;
}>();

const keyboardInset = useKeyboardInset(toRef(props, 'open'));

const emit = defineEmits<{ (e: 'close'): void }>();

const sheetEl = ref<HTMLElement | null>(null);
const backdropEl = ref<HTMLElement | null>(null);
const { handlers } = useSheetDrag({
  sheet: sheetEl,
  backdrop: backdropEl,
  onDismiss: () => emit('close'),
});

const duration = { enter: motionMs('--dur-sheet-in', 440), leave: motionMs('--dur-sheet-out', 280) };

// Focus moves into the sheet when it opens, so Esc closes it and keyboard
// focus starts inside it rather than on the page behind.
watch(() => props.open, async (open) => {
  if (!open) return;
  await nextTick();
  sheetEl.value?.focus({ preventScroll: true });
});
</script>

<template>
  <Teleport to="body">
    <Transition name="bsheet" :duration="duration">
      <div
        v-if="open"
        class="bsheet-root fixed inset-0 z-[150] flex items-end md:items-center justify-center"
        :style="{ paddingBottom: `${keyboardInset}px`, '--keyboard-inset': `${keyboardInset}px` }"
        @keydown.esc="emit('close')"
      >
        <div ref="backdropEl" class="bsheet-backdrop absolute inset-0 bg-[rgba(23,28,25,0.28)]" @click="emit('close')"></div>
        <div
          ref="sheetEl"
          role="dialog"
          aria-modal="true"
          :aria-label="title"
          tabindex="-1"
          class="bsheet-panel outline-none relative w-full md:w-[460px] bg-surface-light rounded-t-sheet md:rounded-sheet shadow-sheet md:shadow-float px-6 pb-[max(env(safe-area-inset-bottom),28px)] md:pb-8"
        >
          <!-- Drag handle: swipe down to close -->
          <div class="touch-none -mx-6 px-6 pt-3 pb-5" v-on="handlers">
            <div class="w-9 h-1 rounded-full bg-line mx-auto mb-5" aria-hidden="true"></div>
            <h3 class="font-serif text-[24px] font-normal leading-tight text-text-main">{{ title }}</h3>
          </div>
          <div class="bsheet-rise">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.bsheet-enter-active .bsheet-backdrop {
  transition: opacity var(--dur-fade) var(--ease-out);
}

.bsheet-enter-active .bsheet-panel {
  transition:
    transform var(--dur-sheet-in) var(--ease-drawer),
    opacity var(--dur-fade) var(--ease-out);
}

.bsheet-leave-active {
  pointer-events: none;
}

.bsheet-leave-active .bsheet-backdrop,
.bsheet-leave-active .bsheet-panel {
  transition:
    transform var(--dur-sheet-out) var(--ease-drawer),
    opacity var(--dur-sheet-out) var(--ease-out);
}

/* Moves above the keyboard as it opens and back down as it closes. */
.bsheet-root {
  transition: padding-bottom var(--dur-popover) var(--ease-out);
}

/* The form follows the panel a beat later (runs once, on creation). */
.bsheet-rise {
  animation: bsheetRise var(--dur-enter) var(--ease-out) 90ms backwards;
}

@keyframes bsheetRise {
  from {
    opacity: 0;
    transform: translate3d(0, 10px, 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .bsheet-rise {
    animation: none;
  }
}

.bsheet-enter-from .bsheet-backdrop,
.bsheet-leave-to .bsheet-backdrop {
  opacity: 0;
}

/* Phones: up from the bottom edge and back down. */
.bsheet-enter-from .bsheet-panel,
.bsheet-leave-to .bsheet-panel {
  transform: translate3d(0, 100%, 0);
}

/* iPad: a centred card rises a little and fades, rather than travelling. */
@media (min-width: 768px) {
  .bsheet-enter-from .bsheet-panel {
    opacity: 0;
    transform: translate3d(0, 16px, 0) scale(0.97);
  }

  .bsheet-leave-to .bsheet-panel {
    opacity: 0;
    transform: scale(0.98);
  }
}
</style>
