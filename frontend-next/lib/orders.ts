import { getApiBaseUrl, readStoredToken } from './auth';

export type ImportedReviewReason =
  | 'overdue_payment_risk'
  | 'invoice_missing_fields'
  | 'missing_contact_details'
  | 'unlinked_contact';

export type QueueOrder = {
  id: string;
  order_number: string;
  status: string;
  due_date: string;
  payment_status: string;
  total_amount: number;
  delivery_method?: string | null;
  customer_summary: {
    contact_id?: string | null;
    name?: string | null;
    email?: string | null;
    phone?: string | null;
    is_linked_contact?: boolean;
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
    next_step?: string;
    supporting_items?: string[];
  };
};

export type OrderDetailRecord = QueueOrder & {
  is_imported: boolean;
  import_source?: string | null;
  legacy_status_raw?: string | null;
  needs_review?: boolean | null;
  review_reasons: ImportedReviewReason[];
  primary_review_reason?: ImportedReviewReason | null;
  review_next_check?: string | null;
  invoice_summary: {
    is_ready?: boolean;
    status: string;
    missing_fields?: string[];
    pdf_path?: string | null;
    client_portal_path?: string | null;
  };
  review_focus_summary: {
    order_number: string;
    customer_name: string;
    due_label: string;
    status_label: string;
    item_summary: string;
    item_count_label: string;
    payment_confidence: string;
    invoice_confidence: string;
    handoff_confidence: string;
    payment_trust_preview?: string | null;
    missing_basics: string[];
    risk_note: string;
    next_step: string;
    next_step_detail: string;
  };
  payment_focus_summary: {
    amount_owed_now?: number;
    payment_state: string;
    collection_stage: string;
    deposit_status: string;
    balance_status: string;
    due_timing: string;
    risk_note: string;
    next_step: string;
    next_step_detail: string;
    trust_state: string;
    trust_label: string;
    trust_note: string;
    historical_payment_label?: string | null;
    historical_payment_note?: string | null;
  };
  invoice_focus_summary: {
    status_label: string;
    readiness_note: string;
    order_identity: string;
    customer_identity: string;
    amount_summary: string;
    payment_context: string;
    blockers: string[];
    missing_basics: string[];
    next_step: string;
    next_step_detail: string;
  };
  handoff_focus_summary: {
    handoff_time_label: string;
    method_status: string;
    method_label: string;
    contact_name: string;
    primary_contact: string;
    secondary_contact: string;
    destination_label: string;
    destination_detail: string;
    readiness_note: string;
    missing_basics: string[];
    next_step: string;
    next_step_detail: string;
  };
  production_focus_summary: {
    readiness_label: string;
    missing_basics: string[];
    attention_note: string;
    next_step: string;
    next_step_detail: string;
  };
  contact_focus_summary: {
    readiness_label: string;
    missing_basics: string[];
    attention_note: string;
    next_step: string;
    next_step_detail: string;
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

export async function fetchOrdersQueue(): Promise<QueueOrder[]> {
  const response = await fetch(`${getApiBaseUrl()}/orders/`, {
    headers: buildAuthHeaders(),
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error('Unable to load orders queue');
  }

  return response.json();
}

export async function fetchOrderDetail(orderId: string): Promise<OrderDetailRecord> {
  const response = await fetch(`${getApiBaseUrl()}/orders/${orderId}`, {
    headers: buildAuthHeaders(),
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error('Unable to load order detail');
  }

  return response.json();
}
