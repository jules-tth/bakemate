import axios, { AxiosError } from 'axios';
import type { AxiosRequestConfig, AxiosRequestHeaders } from 'axios';

const apiBaseUrl = import.meta.env.VITE_API_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  config.headers = config.headers ?? {};
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (config.data instanceof FormData) {
    if ('Content-Type' in config.headers) {
      delete (config.headers as AxiosRequestHeaders)['Content-Type'];
    }
  } else if (!('Content-Type' in config.headers)) {
    config.headers['Content-Type'] = 'application/json';
  }
  return config;
});

export const redirectToLogin = () => {
  window.location.assign('/login');
};

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export const refreshAccessToken = async (
  refreshToken: string,
): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data;
};

export const handleApiError = async (
  error: AxiosError,
  redirect: () => void = redirectToLogin,
) => {
  if (error.response?.status === 401) {
    if (error.config) {
      const refresh = localStorage.getItem('refreshToken');
      const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
      if (refresh && !originalRequest._retry) {
        originalRequest._retry = true;
        try {
          const { access_token, refresh_token } = await refreshAccessToken(refresh);
          localStorage.setItem('token', access_token);
          localStorage.setItem('refreshToken', refresh_token);
          apiClient.defaults.headers.common.Authorization = `Bearer ${access_token}`;
          originalRequest.headers = {
            ...originalRequest.headers,
            Authorization: `Bearer ${access_token}`,
          };
          return apiClient.request(originalRequest);
        } catch {
          redirect();
        }
      } else {
        redirect();
      }
    } else {
      redirect();
    }
  }
  console.error(error);
  return Promise.reject(error);
};

export interface OrderItemPayload {
  name: string;
  description?: string;
  quantity: number;
  unit_price: number;
}

export interface OrderRecord {
  id: string;
  order_number: string;
  status: string;
  payment_status: string;
  order_date: string;
  due_date: string;
  deposit_due_date?: string | null;
  balance_due_date?: string | null;
  delivery_method?: string | null;
  notes_to_customer?: string | null;
  internal_notes?: string | null;
  total_amount: number;
  balance_due?: number | null;
  is_imported: boolean;
  legacy_status_raw?: string | null;
  import_source?: string | null;
  review_reasons: ImportedReviewReason[];
  primary_review_reason?: ImportedReviewReason | null;
  review_next_check?: string | null;
  imported_priority_rank: number;
  imported_priority_label?: string | null;
  customer_name?: string | null;
  customer_email?: string | null;
  customer_phone?: string | null;
  customer_summary: {
    contact_id?: string | null;
    name?: string | null;
    email?: string | null;
    phone?: string | null;
    is_linked_contact: boolean;
  };
  payment_summary: {
    amount_paid: number;
    amount_due: number;
    deposit_required: number;
    deposit_outstanding: number;
    balance_due: number;
    is_paid_in_full: boolean;
  };
  invoice_summary: {
    is_ready: boolean;
    status: string;
    missing_fields: string[];
    pdf_path?: string | null;
    client_portal_path?: string | null;
  };
  queue_summary: {
    is_due_today: boolean;
    is_overdue: boolean;
    days_until_due: number;
    due_bucket: string;
    urgency_label: string;
    urgency_rank: number;
  };
  customer_history_summary: {
    total_orders: number;
    completed_orders: number;
    active_orders: number;
    last_order_date?: string | null;
  };
  recent_customer_orders: Array<{
    id: string;
    order_number: string;
    order_date: string;
    due_date: string;
    status: string;
    payment_status: string;
    total_amount: number;
  }>;
  risk_summary: {
    level: string;
    reasons: string[];
    overdue_amount: number;
    outstanding_amount: number;
    has_overdue_payment: boolean;
  };
  payment_focus_summary: {
    amount_owed_now: number;
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
  handoff_focus_summary: {
    handoff_time_label: string;
    method_status: string;
    method_label: string;
    contact_name?: string | null;
    primary_contact: string;
    secondary_contact?: string | null;
    destination_label: string;
    destination_detail: string;
    readiness_note: string;
    missing_basics: string[];
    next_step: string;
    next_step_detail: string;
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
  production_focus_summary: {
    contents_summary: string;
    item_count_label: string;
    readiness_label: string;
    missing_basics: string[];
    attention_note: string;
    next_step: string;
    next_step_detail: string;
  };
  contact_focus_summary: {
    customer_display_name: string;
    best_contact_methods_summary: string;
    readiness_label: string;
    missing_basics: string[];
    attention_note: string;
    next_step: string;
    next_step_detail: string;
  };
  day_running_focus_summary: {
    readiness_label: string;
    reason_summary: string;
    primary_blocker_category: string;
    primary_blocker_label: string;
    queue_reason_preview?: string | null;
    queue_next_step_preview?: string | null;
    queue_payment_trust_preview?: string | null;
    queue_contact_preview?: string | null;
    queue_payment_preview?: string | null;
    queue_handoff_preview?: string | null;
    queue_production_preview?: string | null;
    queue_invoice_preview?: string | null;
    queue_review_preview?: string | null;
    next_step: string;
    supporting_items: string[];
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
  ops_summary: {
    next_action: string;
    ops_attention: string;
    action_class: string;
    primary_cta_label: string;
    primary_cta_path: string;
    primary_cta_panel: string;
  };
  items: Array<{
    id: string;
    name: string;
    description?: string | null;
    quantity: number;
    unit_price: number;
    total_price: number;
  }>;
}

export type ImportedReviewReason =
  | 'overdue_payment_risk'
  | 'invoice_missing_fields'
  | 'missing_contact_details'
  | 'unlinked_contact';

export type DayRunningTriageFilter = 'blocked' | 'needs_attention' | 'ready';

export interface ImportedOrderQueueSummary {
  all_imported_count: number;
  needs_review_count: number;
  no_current_review_count: number;
  review_reason_counts: Record<ImportedReviewReason, number>;
}

export interface DayRunningQueueSummary {
  all_count: number;
  blocked_count: number;
  needs_attention_count: number;
  ready_count: number;
}

export interface CreateOrderPayload {
  due_date: string;
  delivery_method?: string;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
  deposit_amount?: number;
  notes_to_customer?: string;
  internal_notes?: string;
  items: OrderItemPayload[];
}

export interface ListOrdersParams {
  skip?: number;
  limit?: number;
  status?: string;
  imported_only?: boolean;
  search?: string;
  needs_review?: boolean;
  review_reason?: ImportedReviewReason;
  day_running?: DayRunningTriageFilter;
  action_class?: string;
  urgency?: string;
}

export const ordersApi = {
  async list(params?: ListOrdersParams) {
    const response = await apiClient.get<OrderRecord[]>('/orders/', { params });
    return response.data;
  },
  async getImportedSummary(search?: string) {
    const response = await apiClient.get<ImportedOrderQueueSummary>('/orders/imported/summary', {
      params: {
        search: search || undefined,
      },
    });
    return response.data;
  },
  async getDayRunningSummary(params?: ListOrdersParams) {
    const response = await apiClient.get<DayRunningQueueSummary>('/orders/day-running/summary', {
      params,
    });
    return response.data;
  },
  async get(orderId: string) {
    const response = await apiClient.get<OrderRecord>(`/orders/${orderId}`);
    return response.data;
  },
  async create(payload: CreateOrderPayload) {
    const response = await apiClient.post<OrderRecord>('/orders/', payload);
    return response.data;
  },
};

apiClient.interceptors.response.use((response) => response, handleApiError);

export default apiClient;
