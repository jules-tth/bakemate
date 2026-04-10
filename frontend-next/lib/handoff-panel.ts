import type { OrderDetailRecord } from './orders';

export function getHandoffMethodTone(methodStatus: string): string {
  switch (methodStatus) {
    case 'Method confirmed':
      return 'badge badge-success';
    case 'Method needs confirmation':
      return 'badge badge-warn';
    default:
      return 'badge';
  }
}

export function getHandoffDestinationSummary(order: OrderDetailRecord): string {
  const destination = order.handoff_focus_summary.destination_label.trim();
  const detail = order.handoff_focus_summary.destination_detail.trim();

  if (!detail || detail === destination) {
    return destination;
  }

  return `${destination} · ${detail}`;
}

export function getHandoffContactLines(order: OrderDetailRecord): string[] {
  return [
    order.handoff_focus_summary.contact_name,
    order.handoff_focus_summary.primary_contact,
    order.handoff_focus_summary.secondary_contact,
  ].filter((value) => value && value.trim().length > 0);
}
