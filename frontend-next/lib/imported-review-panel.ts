import type { ImportedReviewReason, OrderDetailRecord } from './orders';

export function describeImportReviewReason(reason?: ImportedReviewReason | null): string {
  switch (reason) {
    case 'overdue_payment_risk':
      return 'Overdue payment risk';
    case 'invoice_missing_fields':
      return 'Invoice data needs review';
    case 'missing_contact_details':
      return 'Contact details missing';
    case 'unlinked_contact':
      return 'Customer link needs review';
    default:
      return 'Review needed';
  }
}

export function getImportedReviewReasons(order: OrderDetailRecord): string[] {
  return order.review_reasons.map((reason) => describeImportReviewReason(reason));
}

export function getImportedReviewSummary(order: OrderDetailRecord): string {
  if (!order.is_imported) {
    return 'This order was created in BakeMate and does not need imported-data review.';
  }

  if (!order.needs_review) {
    return 'No current imported-data review flags are open for this order.';
  }

  return describeImportReviewReason(order.primary_review_reason);
}
