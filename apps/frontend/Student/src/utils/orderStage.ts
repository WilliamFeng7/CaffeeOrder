/**
 * orderStage.ts
 *
 * 进行中订单的阶段 (Stage of an open order): 排队中 / 制作中 / 请取餐, as a label
 * plus how far along the three-step bar is. Shared by the Pickup page and the
 * order strip on Home.
 */
import type { Order } from '../types';

export interface StageLabels {
  queued: string;
  preparing: string;
  ready: string;
}

export const orderStage = (order: Order, t: StageLabels): { label: string; step: number; progress: number } => {
  if (order.stage === 'ready') return { label: t.ready, step: 2, progress: 1 };
  if (order.stage === 'processing') return { label: t.preparing, step: 1, progress: 0.56 };
  return { label: t.queued, step: 0, progress: 0.14 };
};
