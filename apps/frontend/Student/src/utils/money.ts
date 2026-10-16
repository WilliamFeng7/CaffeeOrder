/**
 * Money helpers.
 *
 * The backend stores every amount as an integer number of cents (分). The API
 * layer divides by 100 for display, which leaves floating-point yuan values
 * behind - and summing those drifts (0.1 + 0.2 === 0.30000000000000004), so a
 * cart total could show one cent away from the amount the server actually
 * charges.
 *
 * Rule: keep arithmetic in integer cents and only convert to a display string at
 * the last step.
 */

export const CENT = 100;

/** Convert a yuan amount (possibly a float from the API) to integer cents. */
export function toCents(yuan: number): number {
  return Math.round(Number(yuan) * CENT);
}

/** Format integer cents as a yuan display string, e.g. 1550 -> "15.50". */
export function formatCents(cents: number): string {
  return (cents / CENT).toFixed(2);
}

/**
 * Sum line items in integer cents.
 * Accepts anything exposing `price` (yuan) and `quantity`.
 */
export function sumCents(
  items: ReadonlyArray<{ price: number; quantity: number }>
): number {
  return items.reduce((total, item) => total + toCents(item.price) * item.quantity, 0);
}

/**
 * A menu price for browsing: "¥15" for whole yuan, "¥15.50" otherwise (the
 * checkout and receipts keep formatCents' exact two decimals).
 */
export function menuPrice(yuan: number): string {
  const cents = toCents(yuan);
  return `¥${cents % CENT === 0 ? String(cents / CENT) : formatCents(cents)}`;
}
