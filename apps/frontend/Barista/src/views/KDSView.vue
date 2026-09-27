<script setup lang="ts">
/**
 * KDSView.vue
 *
 * Kitchen Display System order board: three columns (new / making / ready)
 * under a row of plain numbers.
 *
 * Motion: counts roll and stats count to their new value; a card glides out
 * of one column and into the next; an order that has just arrived flashes a
 * soft highlight once (and the device beeps).
 */
import AppIcon from '@shared/components/AppIcon.vue';
import AnimatedNumber from '@shared/components/AnimatedNumber.vue';
import RollingNumber from '@shared/components/RollingNumber.vue';
import { ref, reactive, watch, onMounted, onUnmounted, computed } from 'vue';
import { api } from '../api';
import { useToastStore } from '../stores/toast';
import { useOrderPolling } from '../composables/useOrderPolling';
import { useKitchenDevice } from '../composables/useKitchenDevice';
import OrderCard from '../components/OrderCard.vue';
import KDSLayout from '../components/KDSLayout.vue';

const toast = useToastStore();

// Global tick for OrderCard time updates (instead of per-card intervals)
const globalTick = ref(0);
let tickInterval: number | null = null;

// Screen stays awake, and the new-order beep works on the iPad (see the composable).
const { soundReady, beep } = useKitchenDevice();

// Polling (no overlap, pauses while hidden, aborts on unmount) lives in the
// shared composable.
const { orders, loading, refreshing, syncCount, refresh } = useOrderPolling({
    interval: 8000,
    onNewOrders: (count) => {
        beep();
        toast.info(`${count} new order(s)!`);
    },
});

// Orders that arrived after the board was first loaded flash once. Ids leave
// the set after the flash, so a card moving to the next column does not
// flash again.
const known = new Set<number>();
let primed = false;
const fresh = reactive(new Set<number>());
watch(orders, (list) => {
    for (const o of list) {
        if (known.has(o.id)) continue;
        known.add(o.id);
        if (!primed) continue;
        fresh.add(o.id);
        window.setTimeout(() => fresh.delete(o.id), 2000);
    }
    if (list.length) primed = true;
});

const handleStatusUpdate = async (orderId: number, status: string) => {
    // Staff call orders by pickup number, not by database id.
    const order = orders.value.find(o => o.id === orderId);
    const label = order?.pickup_number != null ? `#${order.pickup_number}` : `#${orderId}`;
    try {
        await api.updateOrderStatus(orderId, status);
        toast.success(`Order ${label} → ${status}`);
        await refresh();
    } catch (e) {
        toast.error('Failed to update status');
    }
};

// Backend statuses: created / processing / ready / completed / refunded
const pendingOrders = computed(() => orders.value.filter(o => o.status.toLowerCase() === 'created'));
const processingOrders = computed(() => orders.value.filter(o => o.status.toLowerCase() === 'processing'));
const completedOrders = computed(() => orders.value.filter(o => o.status.toLowerCase() === 'ready'));

// Stats
// The feed also carries older orders (finished ones, and any backlog left from
// previous days), so "today" is filtered on the order date. Counting the whole
// feed showed every order ever loaded, and averaging a months-old backlog into
// the wait time produced hundreds of thousands of minutes.
const isToday = (iso: string) => new Date(iso).toDateString() === new Date().toDateString();
const totalOrders = computed(() => orders.value.filter(o => isToday(o.created_at)).length);
const avgWaitTime = computed(() => {
  const activeTimes = [...pendingOrders.value, ...processingOrders.value]
    .filter(o => isToday(o.created_at))
    .map(o => Math.floor((Date.now() - new Date(o.created_at).getTime()) / 60000));
  if (activeTimes.length === 0) return null;
  return Math.round(activeTimes.reduce((a, b) => a + b, 0) / activeTimes.length);
});

const stats = computed(() => [
  { label: 'Today', value: totalOrders.value },
  { label: 'Active', value: pendingOrders.value.length + processingOrders.value.length },
  { label: 'Avg wait', value: avgWaitTime.value, unit: 'min' },
  { label: 'Ready', value: completedOrders.value.length },
]);

// Keyboard shortcuts
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'r' && !e.ctrlKey && !e.metaKey) {
    refresh();
  }
};

// Polling lifecycle (start/stop, visibility pause, abort on unmount) is owned by
// useOrderPolling, which registers its own mounted/unmounted hooks.
onMounted(() => {
    // Global tick every 30s for OrderCard time updates
    tickInterval = setInterval(() => { globalTick.value++; }, 30000) as unknown as number;
    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    if (tickInterval) clearInterval(tickInterval);
    window.removeEventListener('keydown', handleKeydown);
});

const columns = [
  { title: 'New', orders: pendingOrders },
  { title: 'Making', orders: processingOrders },
  { title: 'Ready', orders: completedOrders },
];

const manualRefresh = () => refresh();
</script>

<template>
  <KDSLayout :sound-ready="soundReady" :beat="syncCount">
    <div class="flex flex-col h-full gap-3 md:gap-5">

      <!-- Stats: plain numbers separated by hairlines, refresh at the end -->
      <div class="flex items-stretch gap-2 md:gap-3 animate-slide-up-content">
        <div class="card grid grid-cols-2 md:grid-cols-4 flex-1 min-w-0 divide-line [&>*]:border-line max-md:[&>*:nth-child(n+3)]:border-t md:divide-x">
          <div v-for="(s, i) in stats" :key="s.label" class="px-4 md:px-6 py-3 md:py-4 min-w-0" :class="{ 'max-md:border-l': i % 2 === 1 }">
            <p class="eyebrow">{{ s.label }}</p>
            <p class="mt-1.5 font-serif text-[26px] md:text-[30px] font-medium leading-none tabular-nums">
              <template v-if="s.value !== null">
                <AnimatedNumber :value="s.value" />
                <span v-if="s.unit" class="ml-1 font-sans text-[13px] text-text-sub">{{ s.unit }}</span>
              </template>
              <template v-else>—</template>
            </p>
          </div>
        </div>

        <!-- Refresh (R on a keyboard does the same) -->
        <button
          type="button"
          @click="manualRefresh"
          :disabled="refreshing"
          aria-label="Refresh"
          title="Refresh (R)"
          class="card shrink-0 w-14 md:w-16 flex items-center justify-center text-text-sub hover:text-text-main disabled:opacity-60"
        >
          <AppIcon name="refresh" weight="light" class="text-[22px]" :class="{ 'animate-spin': refreshing }" />
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="flex flex-col items-center gap-4 animate-fade-in">
          <div class="size-8 rounded-full border-[1.5px] border-line border-t-text-main animate-spin"></div>
          <span class="text-[13px] text-text-sub">Loading orders…</span>
        </div>
      </div>

      <!-- Three columns side by side from iPad portrait up, so every status stays in view -->
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 flex-1 min-h-0">
        <section
          v-for="(col, idx) in columns"
          :key="col.title"
          class="flex flex-col h-full min-h-[320px] md:min-h-0 min-w-0 rounded-card bg-cream/70 p-2.5 md:p-3 animate-slide-up-content"
          :style="{ animationDelay: `${60 + idx * 60}ms` }"
        >
          <!-- Column header -->
          <div class="flex items-center justify-between gap-3 px-2 pt-1 pb-3">
            <h2 class="text-[15px] font-medium">{{ col.title }}</h2>
            <span class="min-w-7 h-7 px-2 rounded-full bg-surface-light border border-line text-[13px] font-medium flex items-center justify-center">
              <RollingNumber :value="col.orders.value.length" />
            </span>
          </div>

          <!-- Scrollable order list (TransitionGroup uses the shared .list-* styles) -->
          <TransitionGroup tag="div" name="list" class="flex-1 overflow-y-auto no-scrollbar scroll-smooth-touch relative space-y-2.5">
            <OrderCard
              v-for="order in col.orders.value"
              :key="order.id"
              :order="order"
              :global-tick="globalTick"
              :fresh="fresh.has(order.id)"
              @update-status="handleStatusUpdate"
            />

            <!-- Empty State -->
            <div v-if="col.orders.value.length === 0" key="empty" class="h-40 md:h-48 flex flex-col items-center justify-center gap-2 text-text-sub animate-fade-in">
              <AppIcon name="coffee" weight="light" class="text-2xl opacity-60" />
              <span class="text-[13px]">No orders</span>
            </div>
          </TransitionGroup>
        </section>
      </div>
    </div>
  </KDSLayout>
</template>
