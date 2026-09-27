<script setup lang="ts">
/**
 * An on/off switch. The knob springs across (transform only) and the track
 * colour fades. Keyboard: Space/Enter, like a native checkbox.
 *
 *   <AppSwitch v-model="product.is_recommend" label="设为店长推荐" />
 */
defineProps<{
  modelValue: boolean;
  /** Accessible name (visible text next to it can use aria-labelledby instead). */
  label?: string;
  disabled?: boolean;
}>();

const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>();
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="modelValue"
    :aria-label="label"
    :disabled="disabled"
    class="app-switch relative inline-flex h-7 w-12 shrink-0 items-center rounded-full disabled:opacity-40"
    :class="modelValue ? 'bg-primary' : 'bg-line-strong'"
    @click="emit('update:modelValue', !modelValue)"
  >
    <span
      class="app-switch-knob absolute left-0.5 size-6 rounded-full bg-white shadow-card"
      :class="{ 'is-on': modelValue }"
      aria-hidden="true"
    ></span>
  </button>
</template>

<style scoped>
/* The knob travels on the spring; pressing squashes it slightly wider,
   the way iOS switches do. */
.app-switch-knob {
  transition: transform var(--dur-spring) var(--ease-spring);
}

.app-switch-knob.is-on {
  transform: translate3d(20px, 0, 0);
}

.app-switch:active:not(:disabled) {
  transform: none;
}

.app-switch:active:not(:disabled) .app-switch-knob {
  transform: scaleX(1.12);
  transform-origin: left center;
}

.app-switch:active:not(:disabled) .app-switch-knob.is-on {
  transform: translate3d(20px, 0, 0) scaleX(1.12);
  transform-origin: right center;
}
</style>
