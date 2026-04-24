import { getApiBaseUrl, readStoredToken } from './auth';

export type DayRunningSummary = {
  all_count: number;
  blocked_count: number;
  needs_attention_count: number;
  ready_count: number;
};

export type OpsPreviewOrder = {
  id: string;
  order_number: string;
  status: string;
  due_date: string;
  payment_status: string;
  total_amount: number;
  delivery_method?: string | null;
  customer_summary: {
    name?: string | null;
    email?: string | null;
    phone?: string | null;
  };
  queue_summary: {
    urgency_label: string;
    urgency_rank: number;
    is_overdue: boolean;
    is_due_today: boolean;
    days_until_due: number;
  };
  ops_summary: {
    action_class: string;
    next_action: string;
    ops_attention: string;
    primary_cta_label?: string | null;
    primary_cta_path?: string | null;
    primary_cta_panel?: string | null;
  };
  day_running_focus_summary: {
    readiness_label: string;
    reason_summary: string;
    primary_blocker_label?: string | null;
    queue_reason_preview?: string | null;
    queue_next_step_preview?: string | null;
    queue_payment_trust_preview?: string | null;
  };
};

function buildAuthHeaders() {
  const token = readStoredToken();
  if (!token) {
    throw new Error('Missing auth token');
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

export async function fetchDayRunningSummary(): Promise<DayRunningSummary> {
  const response = await fetch(`${getApiBaseUrl()}/orders/day-running/summary`, {
    headers: buildAuthHeaders(),
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error('Unable to load day-running summary');
  }

  return response.json();
}

export async function fetchOpsPreviewOrders(): Promise<OpsPreviewOrder[]> {
  const response = await fetch(`${getApiBaseUrl()}/orders/`, {
    headers: buildAuthHeaders(),
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error('Unable to load ops preview orders');
  }

  return response.json();
}
