/**
 * Thin re-export of the shared toast store.
 *
 * This file used to be a byte-identical copy in each of the three apps. The
 * implementation now lives in packages/shared/src/toast.ts; the wrapper is kept
 * so every existing `import { useToastStore } from '../stores/toast'` continues
 * to resolve unchanged.
 */
export { useToastStore } from '@shared/toast';
export type { Toast, ToastType } from '@shared/toast';
