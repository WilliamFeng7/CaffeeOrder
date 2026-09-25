<script setup lang="ts">
/**
 * Thin wrapper around the single shared toast renderer.
 *
 * Student and Admin each used to carry their own copy of this component (and
 * Barista had a third inline variant in App.vue). The implementation now lives
 * in packages/shared/src/components/ToastContainer.vue; this file only keeps the
 * existing `./components/ToastContainer.vue` import path working.
 */
import SharedToastContainer from '@shared/components/ToastContainer.vue';
</script>

<template>
  <SharedToastContainer />
</template>
