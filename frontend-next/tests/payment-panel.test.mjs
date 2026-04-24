import test from 'node:test';
import assert from 'node:assert/strict';
import { describeAmountOwedNow, getPaymentTrustTone } from '../lib/payment-panel.ts';

test('bm-087 payment panel explains deposit-stage amount owed now', () => {
  assert.equal(describeAmountOwedNow('deposit_due'), 'Amount owed now reflects the deposit currently due.');
});

test('bm-087 payment panel explains final-balance-stage amount owed now', () => {
  assert.equal(describeAmountOwedNow('balance_due'), 'Amount owed now reflects the final balance currently due.');
});

test('bm-087 payment panel preserves legacy-limited trust tone', () => {
  assert.equal(
    getPaymentTrustTone({ payment_focus_summary: { trust_state: 'legacy_limited' } }),
    'legacy_limited',
  );
});
