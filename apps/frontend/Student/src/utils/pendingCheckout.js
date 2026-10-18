const TERMINAL_NO_CHARGE_CODES = new Set([
  1080001001, // SHOP_CLOSED
  1080002001, // MENU_INVALID
  1080002002, // MENU_UNAVAILABLE
  1080003001, // CUPS_LIMIT
  1080003002, // CARD_DECLINED
  1080003007, // ORDER_REFUNDED
]);
const PENDING_KEY = 'otia.student.pendingCheckouts';

const isAttempt = (value) => value && typeof value === 'object'
  && typeof value.studentNo === 'string' && value.studentNo.trim().length > 0
  && typeof value.key === 'string' && value.key.length > 0 && value.key.length <= 64
  && Array.isArray(value.items);

const hasKey = (value) => value && typeof value === 'object'
  && typeof value.key === 'string' && value.key.length > 0;

function resolveStorage(storage) {
  if (storage !== undefined) return storage;
  try {
    return typeof window === 'undefined' ? null : window.localStorage;
  } catch {
    return null;
  }
}

function readAll(storage) {
  const parsed = JSON.parse(storage.getItem(PENDING_KEY) || '[]');
  if (!Array.isArray(parsed) || parsed.some((value) => hasKey(value) && !isAttempt(value))) return null;
  return parsed.filter(isAttempt);
}

/** Existing keyed state without an account binding cannot safely be replaced. */
export function hasUnscopedPendingCheckout(storage) {
  try {
    storage = resolveStorage(storage);
    if (!storage) return false;
    const parsed = JSON.parse(storage.getItem(PENDING_KEY) || '[]');
    return !Array.isArray(parsed) || parsed.some((value) => hasKey(value) && !isAttempt(value));
  } catch {
    return false;
  }
}

/** Persist the immutable cart payload before sending a charge request. */
export function savePendingCheckout(attempt, storage) {
  try {
    storage = resolveStorage(storage);
    if (!storage || !isAttempt(attempt)) return false;
    const existing = readAll(storage);
    if (!existing) return false;
    const attempts = existing.filter((saved) => saved.studentNo !== attempt.studentNo);
    attempts.push(attempt);
    storage.setItem(PENDING_KEY, JSON.stringify(attempts));
    return true;
  } catch {
    return false;
  }
}

export function loadPendingCheckout(studentNo, storage) {
  try {
    storage = resolveStorage(storage);
    if (!storage || !studentNo) return null;
    const attempts = readAll(storage);
    if (!attempts) return null;
    return attempts.find((attempt) => attempt.studentNo === studentNo) ?? null;
  } catch {
    return null;
  }
}

export function clearPendingCheckout(studentNo, storage) {
  try {
    storage = resolveStorage(storage);
    if (!storage || !studentNo) return;
    const existing = readAll(storage);
    if (!existing) return;
    const attempts = existing.filter((saved) => saved.studentNo !== studentNo);
    if (attempts.length) storage.setItem(PENDING_KEY, JSON.stringify(attempts));
    else storage.removeItem(PENDING_KEY);
  } catch {
    // Retaining a stale key is safer than allowing a retry to create a new order.
  }
}

export function isDefinitiveNoCharge(code) {
  return TERMINAL_NO_CHARGE_CODES.has(code);
}
