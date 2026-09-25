
<script setup lang="ts">
import { RouterView } from 'vue-router'
// Barista used to render its own inline toast list here - a third variant of the
// same component (with no `warning` styling, so warnings fell back to white).
// All three apps now share one renderer.
import ToastContainer from '@shared/components/ToastContainer.vue';
</script>

<template>
  <div id="root" class="bg-background-light overflow-hidden relative">
      <RouterView />
      <ToastContainer />
  </div>
</template>
