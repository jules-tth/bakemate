import type { QueueOrder } from './orders';

export function formatMoney(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

export function formatBakeryDateTime(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(parsed);
}

export function humanizeStatus(value: string) {
  return value.split('_').join(' ');
}

export function getQueueBadge(order: QueueOrder) {
  if (order.queue_summary.is_overdue) {
    return { label: 'Overdue', tone: 'danger' };
  }

  if (order.queue_summary.is_due_today) {
    return { label: 'Due today', tone: 'warn' };
  }

  if (order.queue_summary.days_until_due <= 3) {
    return { label: 'Next up', tone: 'info' };
  }

  return { label: 'Upcoming', tone: 'neutral' };
}

export function getActionClassMeta(actionClass: string) {
  switch (actionClass) {
    case 'payment_now':
      return { label: 'Payment now', tone: 'danger' };
    case 'invoice_blocked':
      return { label: 'Invoice blocked', tone: 'violet' };
    case 'handoff_today':
      return { label: 'Handoff today', tone: 'warn' };
    default:
      return { label: 'Watch', tone: 'neutral' };
  }
}

export function getDayRunningPanelTone(readinessLabel: string) {
  switch (readinessLabel) {
    case 'Ready for today':
      return 'success';
    case 'Needs attention today':
      return 'warn';
    default:
      return 'danger';
  }
}

export function getSortedOrdersQueue(orders: QueueOrder[]) {
  return [...orders].sort((left, right) => {
    const urgencyDelta = left.queue_summary.urgency_rank - right.queue_summary.urgency_rank;
    if (urgencyDelta !== 0) {
      return urgencyDelta;
    }

    return new Date(left.due_date).getTime() - new Date(right.due_date).getTime();
  });
}

export function getCurrentFrontendHref(path: string) {
  const baseUrl = process.env.NEXT_PUBLIC_CURRENT_FRONTEND_URL;
  if (!baseUrl) {
    return null;
  }

  return `${baseUrl.replace(/\/$/, '')}${path}`;
}
