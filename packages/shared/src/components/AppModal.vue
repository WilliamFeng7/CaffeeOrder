<script setup lang="ts">
/**
 * Centered dialog with a real exit. The panel rises and scales in on the
 * strong ease-out while the backdrop fades; closing takes ~65% of that. The
 * old modals were `v-if` blocks that vanished instantly on close.
 *
 * Esc and a backdrop tap close it (unless `dismissible` is false); focus moves
 * into the dialog on open and back to whatever opened it on close.
 *
 *   <AppModal :open="show" title="编辑用户" @close="show = false">
 *     …fields…
 *     <template #footer><button class="btn btn-primary">保存</button></template>
 *   </AppModal>
 */
import { ref, watch, nextTick, computed } from 'vue';
import AppIcon from './AppIcon.vue';
import { motionMs } from '../motion';

const props = withDefaults(defineProps<{
  open: boolean;
  title?: string;
  /** Small line under the title. */
  subtitle?: string;
  size?: 'sm' | 'md' | 'lg';
  dismissible?: boolean;
  closeLabel?: string;
}>(), {
  title: undefined,
  subtitle: undefined,
  size: 'md',
  dismissible: true,
  closeLabel: '关闭',
});

const emit = defineEmits<{ (e: 'close'): void; (e: 'after-leave'): void }>();

const panel = ref<HTMLElement | null>(null);
let opener: HTMLElement | null = null;

const width = computed(() => ({ sm: 'max-w-sm', md: 'max-w-lg', lg: 'max-w-2xl' })[props.size]);

// The panel's own transitions are longer than the root's fade, so Vue is told
// the real durations instead of reading them off the root element.
const duration = computed(() => ({
  enter: motionMs('--dur-scale-in', 460),
  leave: motionMs('--dur-sheet-out', 380),
}));

watch(() => props.open, async (open) => {
  if (open) {
    opener = document.activeElement as HTMLElement | null;
    await nextTick();
    const first = panel.value?.querySelector<HTMLElement>('input, select, textarea');
    (first ?? panel.value)?.focus({ preventScroll: true });
  } else {
    opener?.focus?.({ preventScroll: true });
    opener = null;
  }
}, { immediate: true });

const dismiss = () => {
  if (props.dismissible) emit('close');
};
</script>

<template>
  <Teleport to="body">
    <Transition name="modal" :duration="duration" @after-leave="emit('after-leave')">
      <div
        v-if="open"
        class="fixed inset-0 z-[200] flex items-center justify-center p-4"
        @keydown.esc="dismiss"
      >
        <div class="modal-backdrop absolute inset-0 bg-[rgba(23,28,25,0.28)]" @click="dismiss"></div>
        <div
          ref="panel"
          role="dialog"
          aria-modal="true"
          :aria-label="title"
          tabindex="-1"
          class="modal-panel relative w-full max-h-[88vh] overflow-y-auto bg-surface-light rounded-sheet shadow-float outline-none"
          :class="width"
        >
          <header v-if="title" class="modal-rise flex items-start justify-between gap-4 px-7 pt-7" style="animation-delay: 70ms">
            <div class="min-w-0">
              <h3 class="font-serif text-[24px] font-medium leading-tight text-text-main">{{ title }}</h3>
              <p v-if="subtitle" class="mt-1 text-[13px] text-text-sub">{{ subtitle }}</p>
            </div>
            <button v-if="dismissible" type="button" class="icon-btn -mr-2 -mt-1" :aria-label="closeLabel" @click="emit('close')">
              <AppIcon name="x" weight="light" class="text-xl" />
            </button>
          </header>
          <div class="modal-rise px-7 pb-7" :class="title ? 'pt-6' : 'pt-7'" style="animation-delay: 110ms">
            <slot />
          </div>
          <footer v-if="$slots.footer" class="modal-rise flex gap-3 px-7 pb-7" style="animation-delay: 150ms">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Backdrop fades; the panel rises 12px and grows from 97% while fading in,
   and its content follows a beat later (title, body, buttons ~40ms apart).
   Leaving, it shrinks slightly on an accelerating curve, a little faster. */
.modal-enter-active .modal-backdrop {
  transition: opacity var(--dur-fade) var(--ease-out);
}

.modal-enter-active .modal-panel {
  transition:
    opacity var(--dur-fade) var(--ease-out),
    transform var(--dur-scale-in) var(--ease-out);
}

.modal-leave-active {
  pointer-events: none;
}

.modal-leave-active .modal-backdrop,
.modal-leave-active .modal-panel {
  transition:
    opacity var(--dur-sheet-out) var(--ease-in),
    transform var(--dur-sheet-out) var(--ease-in);
}

.modal-enter-from .modal-backdrop,
.modal-leave-to .modal-backdrop {
  opacity: 0;
}

.modal-enter-from .modal-panel {
  opacity: 0;
  transform: translate3d(0, 12px, 0) scale(0.97);
}

.modal-leave-to .modal-panel {
  opacity: 0;
  transform: scale(0.96);
}

/* Follow-through: runs once when the dialog is created (it is v-if'd), so
   it is independent of the enter classes Vue removes. */
.modal-rise {
  animation: modalRise var(--dur-scale-in) var(--ease-out) backwards;
}

@keyframes modalRise {
  from {
    opacity: 0;
    transform: translate3d(0, 8px, 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .modal-rise {
    animation: none;
  }
}
</style>
