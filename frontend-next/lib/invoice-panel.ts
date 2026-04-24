import type { OrderDetailRecord } from './orders';

export function humanizeInvoiceStatus(statusLabel: string) {
  switch (statusLabel) {
    case 'ready_to_send':
      return 'Ready to send';
    case 'ready_and_paid':
      return 'Ready and paid';
    case 'blocked':
      return 'Blocked';
    default:
      return statusLabel.replaceAll('_', ' ');
  }
}

export function getInvoiceReadinessTone(order: OrderDetailRecord) {
  switch (order.invoice_focus_summary.status_label) {
    case 'ready_to_send':
    case 'ready_and_paid':
      return 'ready';
    default:
      return 'blocked';
  }
}
