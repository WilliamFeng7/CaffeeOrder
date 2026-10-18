import { onMounted, onUnmounted, ref, shallowRef } from 'vue';
import { NETWORK_ERROR, YudaoError } from '@shared/yudao-client';
import { fetchBoard, STATUS_DONE, STATUS_MAKING, type BaristaOrder, type Board } from '../api';

/** 每 4 秒向后端要一次看板。 */
const POLL_MS = 4000;
/** 后端最多返回当天最近制作完成的 10 单。 */
const RECENT_DONE_LIMIT = 10;

export interface BoardProblem {
    msg: string;
    /** 连不上服务器（断网、超时），不是后端拒绝。 */
    offline: boolean;
}

/**
 * 订单看板：轮询、页面切到后台时暂停，回到前台或网络恢复时马上刷新。
 * 第一次加载之后才出现的待录单算作新订单，交给 onNewOrders。
 */
export function useBoard(onNewOrders: (orders: BaristaOrder[]) => void) {
    const board = shallowRef<Board>({ waiting: [], making: [], recentDone: [] });
    const loaded = ref(false);
    const problem = ref<BoardProblem | null>(null);
    /** 上次成功刷新的时间（毫秒）。 */
    const syncedAt = ref<number | null>(null);

    let seen: Set<number> | null = null;
    let controller: AbortController | null = null;
    let timer: number | undefined;
    let running = false;

    async function refresh() {
        window.clearTimeout(timer);
        controller?.abort();
        const current = new AbortController();
        controller = current;
        try {
            const next = await fetchBoard(current.signal);
            if (current.signal.aborted) return;
            announce(next);
            board.value = next;
            loaded.value = true;
            problem.value = null;
            syncedAt.value = Date.now();
        } catch (error) {
            if (current.signal.aborted) return;
            problem.value = error instanceof YudaoError
                ? { msg: error.msg, offline: error.code === NETWORK_ERROR }
                : { msg: '看板加载失败，正在重试', offline: false };
        } finally {
            // 被更新的一次刷新取代时，由那一次负责排下一轮。
            if (controller === current) {
                controller = null;
                if (running && document.visibilityState === 'visible') timer = window.setTimeout(refresh, POLL_MS);
            }
        }
    }

    function announce(next: Board) {
        if (seen) {
            const known = seen;
            const arrived = next.waiting.filter((order) => !known.has(order.id));
            if (arrived.length) onNewOrders(arrived);
        } else {
            seen = new Set();
        }
        for (const order of [...next.waiting, ...next.making, ...next.recentDone]) seen.add(order.id);
    }

    /** 本机操作成功后先把这一单放到新位置，再马上向后端要一次最新的看板。 */
    function settle(changed: BaristaOrder) {
        const others = (list: BaristaOrder[]) => list.filter((order) => order.id !== changed.id);
        const { waiting, making, recentDone } = board.value;
        board.value = {
            waiting: others(waiting),
            making: changed.status === STATUS_MAKING
                ? [...others(making), changed].sort((a, b) => a.createTime - b.createTime || a.id - b.id)
                : others(making),
            recentDone: changed.status === STATUS_DONE
                ? [changed, ...others(recentDone)].slice(0, RECENT_DONE_LIMIT)
                : others(recentDone),
        };
        void refresh();
    }

    function pause() {
        window.clearTimeout(timer);
        controller?.abort();
        controller = null;
    }

    const onVisibility = () => {
        if (document.visibilityState === 'visible') void refresh();
        else pause();
    };
    const onOnline = () => void refresh();

    onMounted(() => {
        running = true;
        document.addEventListener('visibilitychange', onVisibility);
        window.addEventListener('online', onOnline);
        void refresh();
    });

    onUnmounted(() => {
        running = false;
        document.removeEventListener('visibilitychange', onVisibility);
        window.removeEventListener('online', onOnline);
        pause();
    });

    return { board, loaded, problem, syncedAt, refresh, settle };
}
