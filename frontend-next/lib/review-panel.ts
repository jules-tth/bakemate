import type { OrderDetailRecord } from './orders';

export function getReviewPrimaryBlocker(order: OrderDetailRecord) {
  return order.day_running_focus_summary.primary_blocker_label || order.day_running_focus_summary.reason_summary;
}

export function getReviewCueRows(order: OrderDetailRecord) {
  return [
    {
      label: 'Day-running readiness',
      value: order.day_running_focus_summary.readiness_label,
      detail: order.day_running_focus_summary.reason_summary,
    },
    {
      label: 'Production',
      value: order.production_focus_summary.readiness_label,
      detail: order.production_focus_summary.attention_note,
    },
    {
      label: 'Contact',
      value: order.contact_focus_summary.readiness_label,
      detail: order.contact_focus_summary.attention_note,
    },
    {
      label: 'Payment trust',
      value: order.review_focus_summary.payment_trust_preview || order.payment_focus_summary.trust_label,
      detail: order.payment_focus_summary.trust_note,
    },
  ];
}
