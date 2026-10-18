<script setup lang="ts">
/**
 * 咖啡师端的主界面：当天 App 订单看板。
 *
 * 两列：待录单（最早的一单是整个看板唯一的绿色大卡，咖啡师照着它录进收银系统）、
 * 制作中（收银单号打头，做好了点"制作完成"）。最近完成收在顶栏按钮的抽屉里，点错了从那里撤回。
 * 看板每 4 秒刷新一次（useBoard），来新订单时闪一下并"叮—咚"一声（useCounterDevice）。
 */
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import AppIcon from '@shared/components/AppIcon.vue';
import RollingNumber from '@shared/components/RollingNumber.vue';
import { useToastStore } from '@shared/toast';
import { logout, type BaristaOrder } from '../api';
import { clock } from '../time';
import { useBoard } from '../composables/useBoard';
import { useCounterDevice } from '../composables/useCounterDevice';
import OrderCard from '../components/OrderCard.vue';
import OrderSheet from '../components/OrderSheet.vue';

const toast = useToastStore();

// iPad 屏幕常亮和新订单提示音。
const { soundOn, soundBlocked, chime, toggleSound } = useCounterDevice();

// 第一次加载之后才出现的待录单算新订单：提示音 + toast + 卡片闪一下。
const fresh = reactive(new Set<number>());
const { board, loaded, problem, syncedAt, refresh, settle } = useBoard((orders) => {
    chime();
    toast.info(orders.length > 1 ? `来了 ${orders.length} 张新订单` : `新订单：${orders[0].studentName}`);
    for (const order of orders) {
        fresh.add(order.id);
        window.setTimeout(() => fresh.delete(order.id), 2400);
    }
});

// 卡片上的"已等 x 分钟"每 15 秒走一格；顶栏时钟单独每秒走。
const now = ref(Date.now());
const clockNow = ref(Date.now());
let tick: number | undefined;
let clockTick: number | undefined;
onMounted(() => {
    tick = window.setInterval(() => { now.value = Date.now(); }, 15000);
    clockTick = window.setInterval(() => { clockNow.value = Date.now(); }, 1000);
});
onUnmounted(() => {
    window.clearInterval(tick);
    window.clearInterval(clockTick);
});

const waiting = computed(() => board.value.waiting);
const making = computed(() => board.value.making);
const recentDone = computed(() => board.value.recentDone);

// 最近完成抽屉：平时不占看板的位置，要撤回时才打开。
const doneOpen = ref(false);

// 点开详情的订单按 id 跟踪，轮询拿到最新数据后详情跟着更新；单据不在了（例如被管理端动过）就关掉。
const selectedId = ref<number | null>(null);
const selected = computed(() => {
    if (selectedId.value === null) return null;
    const all = [...board.value.waiting, ...board.value.making, ...board.value.recentDone];
    return all.find((order) => order.id === selectedId.value) ?? null;
});

function onChanged(changed: BaristaOrder) {
    settle(changed);
    selectedId.value = null;
}

// 退出登录是两步的：收银台忙起来容易误触。
const confirmingLogout = ref(false);
let logoutTimer: number | undefined;
async function requestLogout() {
    if (!confirmingLogout.value) {
        confirmingLogout.value = true;
        window.clearTimeout(logoutTimer);
        logoutTimer = window.setTimeout(() => { confirmingLogout.value = false; }, 3000);
        return;
    }
    window.clearTimeout(logoutTimer);
    await logout();
}

/** 最近完成一列的条目概要："拿铁×2、可颂"。 */
const summary = (order: BaristaOrder) =>
    order.items.map((item) => `${item.name}${item.quantity > 1 ? `×${item.quantity}` : ''}`).join('、');
</script>

<template>
<div class="h-full flex flex-col select-none">
  <!-- 顶栏：店名、北京时间、同步状态、提示音开关、退出 -->
  <header class="flex items-center gap-4 px-5 md:px-7 pt-4 pb-3 shrink-0 animate-slide-up-content">
    <div class="flex items-baseline gap-3 min-w-0">
      <h1 class="font-serif text-[22px] font-medium tracking-[-0.01em] whitespace-nowrap">咖啡师端</h1>
      <span class="eyebrow hidden sm:inline">OTIA Café</span>
    </div>
    <p class="font-num text-[20px] font-semibold tabular-nums text-text-sub">{{ clock(clockNow) }}</p>

    <div class="ml-auto flex items-center gap-2">
      <p v-if="problem" class="flex items-center gap-1.5 h-9 px-3.5 rounded-full bg-danger-soft text-danger text-[13px] font-medium">
        <AppIcon :name="problem.offline ? 'speaker-slash' : 'warning'" class="text-[15px]" />
        {{ problem.offline ? '连不上服务器，正在重试' : problem.msg }}
      </p>
      <p v-else-if="syncedAt" class="text-[13px] text-text-sub tabular-nums hidden md:block">已同步 {{ clock(syncedAt) }}</p>

      <button
        type="button"
        class="h-10 pl-4 pr-2 rounded-full bg-surface-light border border-line flex items-center gap-2 text-[14px] font-medium"
        @click="doneOpen = true"
      >
        最近完成
        <span class="min-w-6 h-6 px-1.5 rounded-full bg-cream text-[12px] text-text-sub flex items-center justify-center">
          <RollingNumber :value="recentDone.length" />
        </span>
      </button>

      <button
        type="button"
        class="icon-btn"
        :aria-label="soundOn ? '关闭提示音' : '打开提示音'"
        :title="soundBlocked ? '点一下屏幕后提示音才能出声' : (soundOn ? '关闭提示音' : '打开提示音')"
        @click="toggleSound"
      >
        <AppIcon :name="soundOn ? 'bell' : 'speaker-slash'" weight="light" class="text-[21px]" />
      </button>

      <button
        type="button"
        class="icon-btn"
        :class="{ 'w-auto px-4 text-danger': confirmingLogout }"
        :aria-label="confirmingLogout ? '确认退出登录' : '退出登录'"
        @click="requestLogout"
      >
        <span v-if="confirmingLogout" class="text-[13px] font-medium">确认退出？</span>
        <AppIcon v-else name="sign-out" weight="light" class="text-[20px]" />
      </button>
    </div>
  </header>

  <!-- 第一次打开 -->
  <div v-if="!loaded && !problem" class="flex-1 flex items-center justify-center">
    <div class="flex flex-col items-center gap-4 animate-fade-in">
      <div class="size-8 rounded-full border-[1.5px] border-line border-t-text-main animate-spin"></div>
      <span class="text-[13px] text-text-sub">正在加载订单…</span>
    </div>
  </div>

  <!-- 两列看板：iPad 横屏（≥1024）两列并排，竖屏单列纵向滚动 -->
  <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-3 lg:gap-4 flex-1 min-h-0 px-5 lg:px-7 pb-5 lg:pb-7 overflow-y-auto lg:overflow-hidden">
    <!-- 待录单 -->
    <section class="flex flex-col h-full min-h-[300px] lg:min-h-0 min-w-0 rounded-card bg-cream/70 p-2.5 lg:p-3 animate-slide-up-content" style="animation-delay: 60ms">
      <div class="flex items-center gap-2.5 px-2 pt-1 pb-3">
        <h2 class="text-[15px] font-medium">待录单</h2>
        <span class="min-w-7 h-7 px-2 rounded-full bg-surface-light border border-line text-[13px] font-medium flex items-center justify-center">
          <RollingNumber :value="waiting.length" />
        </span>
        <span v-if="waiting.length" class="text-[12px] text-text-sub">先录最上面这单</span>
      </div>
      <TransitionGroup tag="div" name="list" class="flex-1 overflow-y-auto no-scrollbar scroll-smooth-touch relative flex flex-col gap-2.5">
        <OrderCard
          v-for="(order, index) in waiting"
          :key="order.id"
          :order="order"
          :now="now"
          :variant="index === 0 ? 'next' : 'waiting'"
          :fresh="fresh.has(order.id)"
          @open="selectedId = order.id"
        />
        <div v-if="waiting.length === 0" key="empty" class="h-40 md:h-48 flex flex-col items-center justify-center gap-2 text-text-sub animate-fade-in">
          <AppIcon name="receipt" weight="light" class="text-2xl opacity-60" />
          <span class="text-[13px]">没有待录单的订单</span>
        </div>
      </TransitionGroup>
    </section>

    <!-- 制作中 -->
    <section class="flex flex-col h-full min-h-[300px] lg:min-h-0 min-w-0 rounded-card bg-cream/70 p-2.5 lg:p-3 animate-slide-up-content" style="animation-delay: 120ms">
      <div class="flex items-center gap-2.5 px-2 pt-1 pb-3">
        <h2 class="text-[15px] font-medium">制作中</h2>
        <span class="min-w-7 h-7 px-2 rounded-full bg-surface-light border border-line text-[13px] font-medium flex items-center justify-center">
          <RollingNumber :value="making.length" />
        </span>
      </div>
      <TransitionGroup tag="div" name="list" class="flex-1 overflow-y-auto no-scrollbar scroll-smooth-touch relative flex flex-col gap-2.5">
        <OrderCard
          v-for="order in making"
          :key="order.id"
          :order="order"
          :now="now"
          variant="making"
          :fresh="fresh.has(order.id)"
          @open="selectedId = order.id"
        />
        <div v-if="making.length === 0" key="empty" class="h-40 md:h-48 flex flex-col items-center justify-center gap-2 text-text-sub animate-fade-in">
          <AppIcon name="coffee" weight="light" class="text-2xl opacity-60" />
          <span class="text-[13px]">没有制作中的订单</span>
        </div>
      </TransitionGroup>
    </section>

  </div>

  <!-- 最近完成抽屉：从右侧拉出，点一单可撤回"制作完成" -->
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="doneOpen" class="fixed inset-0 z-30 flex justify-end" role="dialog" aria-modal="true" aria-label="最近完成">
        <div class="drawer-scrim absolute inset-0" @click="doneOpen = false"></div>
        <div class="drawer-panel relative w-full max-w-[420px] h-full flex flex-col bg-background-light">
          <div class="flex items-center gap-3 px-5 pt-5 pb-4 border-b border-line">
            <h2 class="text-[17px] font-semibold">最近完成</h2>
            <span class="min-w-6 h-6 px-1.5 rounded-full bg-cream text-[12px] text-text-sub flex items-center justify-center">
              <RollingNumber :value="recentDone.length" />
            </span>
            <span class="text-[12px] text-text-sub">点错了可以撤回</span>
            <button type="button" class="icon-btn ml-auto -mr-2" aria-label="关闭" @click="doneOpen = false">
              <AppIcon name="x" weight="light" class="text-[20px]" />
            </button>
          </div>
          <div class="flex-1 overflow-y-auto no-scrollbar scroll-smooth-touch p-3 flex flex-col gap-2">
            <button
              v-for="order in recentDone"
              :key="order.id"
              type="button"
              class="done-row"
              @click="selectedId = order.id"
            >
              <span class="font-num text-[19px] font-semibold tabular-nums leading-none">{{ order.posOrderNo }}</span>
              <span class="min-w-0 flex-1 text-left">
                <span class="block text-[14px] font-medium truncate">{{ order.studentName }}</span>
                <span class="block text-[12px] text-text-sub truncate">{{ summary(order) }}</span>
              </span>
              <span v-if="order.doneTime" class="font-num text-[13px] tabular-nums text-text-sub shrink-0">{{ clock(order.doneTime) }}</span>
            </button>
            <div v-if="recentDone.length === 0" class="h-48 flex flex-col items-center justify-center gap-2 text-text-sub animate-fade-in">
              <AppIcon name="check-circle" weight="light" class="text-2xl opacity-60" />
              <span class="text-[13px]">今天还没有完成的订单</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <OrderSheet
    v-if="selected"
    :order="selected"
    :now="now"
    @close="selectedId = null"
    @changed="onChanged"
  />
</div>
</template>

<style scoped>
.done-row {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    padding: 12px 14px;
    border: 1px solid theme('colors.line');
    border-radius: 14px;
    background: theme('colors.surface-light');
    color: theme('colors.text-main');
    text-align: left;
}

.drawer-scrim {
    background: theme('colors.scrim');
}

.drawer-panel {
    box-shadow: -16px 0 40px rgba(23, 28, 25, 0.14);
    padding-top: env(safe-area-inset-top);
    padding-bottom: env(safe-area-inset-bottom);
}

.drawer-enter-active,
.drawer-leave-active {
    transition: opacity var(--dur-enter) var(--ease-out);
}
.drawer-enter-active .drawer-panel {
    transition: transform var(--dur-enter) var(--ease-out);
}
.drawer-leave-active .drawer-panel {
    transition: transform 200ms ease-in;
}
.drawer-enter-from,
.drawer-leave-to {
    opacity: 0;
}
.drawer-enter-from .drawer-panel,
.drawer-leave-to .drawer-panel {
    transform: translateX(64px);
}

@media (prefers-reduced-motion: reduce) {
    .drawer-enter-active,
    .drawer-leave-active,
    .drawer-enter-active .drawer-panel,
    .drawer-leave-active .drawer-panel {
        transition: none;
    }
}
</style>
