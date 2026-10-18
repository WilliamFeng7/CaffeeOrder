import test from 'node:test';
import assert from 'node:assert/strict';
import {
  clearPendingCheckout,
  hasUnscopedPendingCheckout,
  isDefinitiveNoCharge,
  loadPendingCheckout,
  savePendingCheckout,
} from '../src/utils/pendingCheckout.js';

function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
  };
}

test('pending checkout payload and key survive reload and remain student-scoped', () => {
  const storage = memoryStorage();
  const attempt = { studentNo: 'S1', key: 'stable-key', items: [{ itemId: 1, quantity: 2, optionIds: [5] }] };

  assert.equal(savePendingCheckout(attempt, storage), true);
  assert.deepEqual(loadPendingCheckout('S1', storage), attempt);
  assert.equal(loadPendingCheckout('S2', storage), null);
  clearPendingCheckout('S1', storage);
  assert.equal(loadPendingCheckout('S1', storage), null);
});

test('ambiguous and pending errors retain a retry key; only terminal outcomes clear it', () => {
  assert.equal(isDefinitiveNoCharge(-1), false); // network timeout
  assert.equal(isDefinitiveNoCharge(1080003003), false); // PAYMENT_UNKNOWN
  assert.equal(isDefinitiveNoCharge(1080003004), false); // ORDER_PAYING
  assert.equal(isDefinitiveNoCharge(1080003002), true); // CARD_DECLINED
  assert.equal(isDefinitiveNoCharge(1080003007), true); // confirmed refund
});

test('storage failures fail closed before order submission', () => {
  const unavailable = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); } };
  assert.equal(savePendingCheckout({ studentNo: 'S1', key: 'k', items: [] }, unavailable), false);
});

test('an attempt without a loaded student identity cannot be persisted', () => {
  const storage = memoryStorage();
  assert.equal(savePendingCheckout({ studentNo: '', key: 'k', items: [] }, storage), false);
  assert.equal(loadPendingCheckout('S1', storage), null);
});

test('a legacy unscoped payment key is preserved and blocks replacement keys', () => {
  const storage = memoryStorage();
  const legacy = [{ studentNo: '', key: 'possibly-charged-key', items: [{ itemId: 1, quantity: 1 }] }];
  storage.setItem('otia.student.pendingCheckouts', JSON.stringify(legacy));

  assert.equal(hasUnscopedPendingCheckout(storage), true);
  assert.equal(loadPendingCheckout('S1', storage), null);
  assert.equal(savePendingCheckout({ studentNo: 'S1', key: 'new-key', items: [] }, storage), false);
  clearPendingCheckout('S1', storage);
  assert.deepEqual(JSON.parse(storage.getItem('otia.student.pendingCheckouts')), legacy);
});
