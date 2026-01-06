import { shallowRef, ref, onMounted, onUnmounted } from 'vue';
import { api, type Order } from '../api';

interface UseOrderPollingOptions {
    interval?: number;
    onNewOrders?: (count: number) => void;
}

export function useOrderPolling(options: UseOrderPollingOptions = {}) {
    const { interval = 4000, onNewOrders } = options;

    const orders = shallowRef<Order[]>([]);
    const loading = ref(true);
    const refreshing = ref(false);
    const error = ref<Error | null>(null);

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
            const data = await api.getAllOrders();
            const sortedOrders = data.sort((a, b) =>
                new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            );

            // Check for new pending orders
            const newPendingCount = sortedOrders.filter(o =>
                ['pending', 'new'].includes(o.status.toLowerCase())
            ).length;

            if (previousPendingCount > 0 && newPendingCount > previousPendingCount) {
                onNewOrders?.(newPendingCount - previousPendingCount);
            }
            previousPendingCount = newPendingCount;

            orders.value = sortedOrders;
            error.value = null;
        } catch (e) {
            if ((e as Error).name !== 'AbortError') {
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
        refresh
    };
}
