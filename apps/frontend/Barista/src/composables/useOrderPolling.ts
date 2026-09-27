import { shallowRef, ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import { api, type Order } from '../api';

interface UseOrderPollingOptions {
    interval?: number;
    onNewOrders?: (count: number) => void;
}

/**
 * Backend OrderStatus values that count as a *newly arrived* order.
 * The previous check looked for 'pending' / 'new', which this API never returns
 * (it uses created / processing / ready / completed / refunded), so the callback
 * could only ever compare 0 with 0 and never fired.
 */
const NEW_ORDER_STATUSES = ['created'];

export function useOrderPolling(options: UseOrderPollingOptions = {}) {
    const { interval = 4000, onNewOrders } = options;

    const orders = shallowRef<Order[]>([]);
    const loading = ref(true);
    const refreshing = ref(false);
    const error = ref<Error | null>(null);
    // Bumped after every successful fetch (the header's live dot pings on it).
    const syncCount = ref(0);

    let abortController: AbortController | null = null;
    let timeoutId: number | null = null;
    let isVisible = true;
    let previousPendingCount = 0;

    const fetchOrders = async (showRefresh = false) => {
        // Abort any pending request to prevent race conditions
        abortController?.abort();
        abortController = new AbortController();

        if (showRefresh) refreshing.value = true;

        try {
            const data = await api.getAllOrders(abortController.signal);
            const sortedOrders = data.sort((a, b) =>
                new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            );

            // Check for new pending orders
            const newPendingCount = sortedOrders.filter(o =>
                NEW_ORDER_STATUSES.includes(o.status.toLowerCase())
            ).length;

            if (previousPendingCount > 0 && newPendingCount > previousPendingCount) {
                onNewOrders?.(newPendingCount - previousPendingCount);
            }
            previousPendingCount = newPendingCount;

            orders.value = sortedOrders;
            error.value = null;
            syncCount.value++;
        } catch (e) {
            // A cancellation is expected whenever a newer tick superseded this
            // one - it is not an outage and must not surface as an error.
            if (!axios.isCancel(e)) {
                error.value = e as Error;
                console.error('Failed to fetch orders', e);
            }
        } finally {
            loading.value = false;
            refreshing.value = false;
            scheduleNext();
        }
    };

    const scheduleNext = () => {
        if (timeoutId) clearTimeout(timeoutId);
        if (isVisible) {
            timeoutId = window.setTimeout(() => fetchOrders(), interval);
        }
    };

    const handleVisibilityChange = () => {
        const wasHidden = !isVisible;
        isVisible = !document.hidden;

        if (isVisible && wasHidden) {
            // Resume polling immediately when tab becomes visible
            fetchOrders();
        } else if (!isVisible && timeoutId) {
            // Pause polling when tab is hidden
            clearTimeout(timeoutId);
            timeoutId = null;
        }
    };

    const refresh = () => fetchOrders(true);

    onMounted(() => {
        document.addEventListener('visibilitychange', handleVisibilityChange);
        fetchOrders();
    });

    onUnmounted(() => {
        document.removeEventListener('visibilitychange', handleVisibilityChange);
        abortController?.abort();
        if (timeoutId) clearTimeout(timeoutId);
    });

    return {
        orders,
        loading,
        refreshing,
        error,
        syncCount,
        refresh
    };
}
