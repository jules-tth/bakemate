import type { OrderDetailRecord } from './orders';

export function describeAmountOwedNow(collectionStage: string) {
  switch (collectionStage) {
    case 'deposit_due':
    case 'deposit_overdue':
      return 'Amount owed now reflects the deposit currently due.';
    case 'balance_due':
    case 'balance_overdue':
      return 'Amount owed now reflects the final balance currently due.';
    case 'paid_in_full':
      return 'No payment is currently due.';
    default:
      return 'Amount owed now reflects the current payment checkpoint.';
  }
}

export function getPaymentTrustTone(order: OrderDetailRecord) {
  return order.payment_focus_summary.trust_state === 'legacy_limited' ? 'legacy_limited' : 'trusted';
}
