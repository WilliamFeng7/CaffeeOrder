<script setup lang="ts">
/**
 * KDSLayout.vue
 *
 * Kitchen display frame: a quiet header (wordmark, live status, clock, sign
 * out) above the order board. The live dot pings once every time fresh
 * orders arrive from the server, so staff can see the board is alive without
 * a spinner looping forever.
 */
import AppIcon from '@shared/components/AppIcon.vue';
import { useRouter } from 'vue-router';
import { ref, onMounted, onUnmounted } from 'vue';
import { auth } from '@shared/auth';

defineProps<{
  // iOS keeps the new-order beep muted until the screen is tapped once.
  soundReady?: boolean;
  /** Increments on every successful poll. */
  beat?: number;
}>();

const router = useRouter();
const currentTime = ref('');
const currentDate = ref('');

const handleLogout = () => {
  // Shared helper so the recorded role is cleared with the token (a hardcoded
  // key here left the role behind and could re-authorize the next session).
  auth.clearToken();
  router.push('/login');
};

// On a shared kitchen iPad a stray tap in the corner used to sign everyone out.
// The first tap arms the button, a second one within 3s signs out.
const confirmingSignOut = ref(false);
let confirmTimer: number | undefined;
const handleSignOutTap = () => {
  if (confirmingSignOut.value) {
    window.clearTimeout(confirmTimer);
    handleLogout();
    return;
  }
  confirmingSignOut.value = true;
  confirmTimer = window.setTimeout(() => { confirmingSignOut.value = false; }, 3000);
};

const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  currentDate.value = now.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' });
};

let timeInterval: number | null = null;
onMounted(() => {
  updateTime();
  timeInterval = setInterval(updateTime, 1000) as unknown as number;
});

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval);
  window.clearTimeout(confirmTimer);
});
</script>

<template>
  <div class="fixed inset-0 w-full h-full bg-background-light overflow-hidden font-sans text-text-main select-none flex flex-col z-0">

    <!-- Header: one compact row, so the order columns get the screen height -->
    <header class="h-16 md:h-[72px] px-4 md:px-7 flex items-center justify-between gap-4 border-b border-line shrink-0 animate-fade-in">

      <!-- Left: wordmark + live status -->
      <div class="flex items-baseline gap-4 min-w-0">
        <span class="font-serif text-[22px] md:text-[24px] font-semibold tracking-tight">OTIA</span>
        <span class="hidden sm:inline text-[14px] text-text-sub">Kitchen</span>
        <span class="flex items-center gap-2 text-[12px] font-medium text-primary">
          <span class="relative flex size-2 self-center">
            <span :key="beat" class="absolute inset-0 rounded-full bg-primary ping" aria-hidden="true"></span>
            <span class="relative size-2 rounded-full bg-primary" aria-hidden="true"></span>
          </span>
          Live
        </span>
        <Transition name="page">
          <span v-if="!soundReady" class="chip chip-warm self-center">
            <AppIcon name="speaker-slash" weight="light" class="text-sm" />
            Tap to enable sound
          </span>
        </Transition>
      </div>

      <!-- Center: time -->
      <div class="hidden md:flex items-baseline gap-3">
        <span class="font-serif text-[28px] font-medium tabular-nums leading-none">{{ currentTime }}</span>
        <span class="eyebrow">{{ currentDate }}</span>
      </div>

      <!-- Right: time on phones, sign out -->
      <div class="flex items-center gap-3">
        <span class="md:hidden font-serif text-[20px] font-medium tabular-nums">{{ currentTime }}</span>
        <button
          type="button"
          @click="handleSignOutTap"
          :aria-label="confirmingSignOut ? 'Tap again to sign out' : 'Sign out'"
          class="btn h-11 px-5 min-w-[120px]"
          :class="confirmingSignOut ? 'btn-danger' : 'btn-ghost text-text-sub hover:text-text-main'"
        >
          <span class="grid overflow-hidden">
            <Transition name="roll-up">
              <span :key="String(confirmingSignOut)" class="col-start-1 row-start-1">{{ confirmingSignOut ? 'Tap again to sign out' : 'Sign out' }}</span>
            </Transition>
          </span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 w-full overflow-hidden relative z-0 p-3 md:p-5">
      <slot></slot>
    </main>
    <!-- Toasts are rendered globally in App.vue (single renderer) -->
  </div>
</template>
