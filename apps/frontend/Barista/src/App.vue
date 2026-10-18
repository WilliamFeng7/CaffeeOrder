<script setup lang="ts">
import ToastContainer from '@shared/components/ToastContainer.vue';
import { signedIn } from './api';
import BoardView from './views/BoardView.vue';
import LoginView from './views/LoginView.vue';
</script>

<template>
  <div id="root" class="bg-background-light overflow-hidden relative font-sans text-text-main">
    <Transition name="page" mode="out-in">
      <BoardView v-if="signedIn" />
      <LoginView v-else />
    </Transition>
    <ToastContainer />
  </div>
</template>
