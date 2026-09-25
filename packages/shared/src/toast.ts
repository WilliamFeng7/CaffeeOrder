import { defineStore } from 'pinia';
import { ref } from 'vue';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
    id: number;
    message: string;
    type: ToastType;
    duration?: number;
}

/**
 * Shared toast store.
 *
 * This file used to exist three times over - Student/, Admin/ and Barista/ each
 * carried a byte-identical `stores/toast.ts` (verified with `diff`). Each copy
 * kept its own `nextId` counter and its own un-styled queue, so a message could
 * look and behave differently per app and any fix had to be applied three times.
 *
 * Each app now re-exports this store from its own `stores/toast.ts`, which keeps
 * every existing `import { useToastStore } from '../stores/toast'` working while
 * giving the three products one implementation.
 */
export const useToastStore = defineStore('toast', () => {
    const toasts = ref<Toast[]>([]);
    let nextId = 1;

    const removeToast = (id: number) => {
        const index = toasts.value.findIndex(t => t.id === id);
        if (index !== -1) {
            toasts.value.splice(index, 1);
        }
    };

    const addToast = (message: string, type: ToastType = 'info', duration = 3000) => {
        const id = nextId++;
        const toast: Toast = { id, message, type, duration };
        toasts.value.push(toast);

        if (duration > 0) {
            setTimeout(() => {
                removeToast(id);
            }, duration);
        }
    };

    const success = (message: string) => addToast(message, 'success');
    const error = (message: string) => addToast(message, 'error');
    const info = (message: string) => addToast(message, 'info');
    const warning = (message: string) => addToast(message, 'warning');

    return {
        toasts,
        addToast,
        removeToast,
        success,
        error,
        info,
        warning,
    };
});
