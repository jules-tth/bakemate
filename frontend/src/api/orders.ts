import apiClient from './index';
import { getCurrentUser } from './users';
import type { OrdersOverTime, RevenueOverTime } from './dashboard';

interface BackendOrder {
  id: string;
  order_number: string;
  customer_name?: string;
  event_type?: string;
  status: string;
  payment_status?: string;
  order_date: string;
  due_date: string;
  delivery_method?: string;
  total_amount: number;
  subtotal?: number;
  tax?: number;
  balance_due?: number | null;
  deposit_amount?: number | null;
  deposit_due_date?: string | null;
  balance_due_date?: string | null;
  notes_to_customer?: string | null;
  internal_notes?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Order {
  id: string;
  orderNo: string;
  customer: string;
  event: string;
  status: string;
  paymentStatus?: string;
  orderDate: string;
  dueDate: string;
  deliveryMethod: string;
  total: number;
  subtotal?: number;
  tax?: number;
  balanceDue?: number | null;
  depositAmount?: number | null;
  depositDueDate?: string | null;
  balanceDueDate?: string | null;
  notesToCustomer?: string | null;
  internalNotes?: string | null;
  createdAt?: string;
  updatedAt?: string;
  priority: string;
}

export interface OrdersSummaryPoint {
  date: string;
  orders: number;
  revenue: number;
}

export interface OrdersSummaryResponse {
  series: OrdersSummaryPoint[];
  totals: { orders: number; revenue: number };
}

export interface OrdersResponse {
  rows: Order[];
  page: number;
  pageSize: number;
  total: number;
}

export interface OrdersQuery {
  start: string;
  end: string;
  status?: string;
  page: number;
  pageSize: number;
  sort?: string;
  filters?: Record<string, string>;
}

export async function getOrdersSummary(range: string): Promise<OrdersSummaryResponse> {
  const [ordersRes, revenueRes] = await Promise.all([
    apiClient.get<OrdersOverTime[]>('/dashboard/orders', { params: { range } }),
    apiClient.get<RevenueOverTime[]>('/dashboard/revenue', { params: { range } }),
  ]);

  const revenueMap = new Map(revenueRes.data.map((r) => [r.date, r.revenue]));
  const series: OrdersSummaryPoint[] = ordersRes.data.map((o) => ({
    date: o.date,
    orders: o.count,
    revenue: revenueMap.get(o.date) ?? 0,
  }));
  const totals = series.reduce(
    (acc, cur) => ({
      orders: acc.orders + cur.orders,
      revenue: acc.revenue + cur.revenue,
    }),
    { orders: 0, revenue: 0 },
  );
  return { series, totals };
}

export async function getOrders(params: OrdersQuery): Promise<OrdersResponse> {
  const { status, start, end } = params;
  // Fetch all orders in batches (API max limit 200) and then filter by date range client-side
  const batchSize = 200;
  let skip = 0;
  const all: BackendOrder[] = [];
  while (true) {
    const resp = await apiClient.get<BackendOrder[]>('/orders', {
      params: { skip, limit: batchSize, status },
    });
    const batch = resp.data;
    if (!batch.length) break;
    all.push(...batch);
    if (batch.length < batchSize) break;
    skip += batchSize;
  }

  let filtered = all;
  if (start || end) {
    const startTs = start ? Date.parse(start) : Number.NEGATIVE_INFINITY;
    const endTs = end ? Date.parse(end) : Number.POSITIVE_INFINITY;
    filtered = all.filter((o) => {
      const ts = Date.parse(o.due_date);
      return ts >= startTs && ts <= endTs;
    });
  }

  const rows: Order[] = filtered.map((o) => ({
    id: o.id,
    orderNo: o.order_number,
    customer: o.customer_name ?? '',
    event: o.event_type ?? '',
    status: o.status,
    paymentStatus: o.payment_status,
    orderDate: o.order_date,
    dueDate: o.due_date,
    deliveryMethod: o.delivery_method ?? '',
    total: o.total_amount,
    subtotal: o.subtotal,
    tax: o.tax,
    balanceDue: o.balance_due ?? null,
    depositAmount: o.deposit_amount ?? null,
    depositDueDate: o.deposit_due_date ?? null,
    balanceDueDate: o.balance_due_date ?? null,
    notesToCustomer: o.notes_to_customer ?? null,
    internalNotes: o.internal_notes ?? null,
    createdAt: o.created_at,
    updatedAt: o.updated_at,
    priority: 'Normal',
  }));

  return { rows, page: 1, pageSize: rows.length, total: rows.length };
}

export type OrderCreateInput = {
  orderDate: string; // yyyy-MM-dd
  dueDate: string;   // yyyy-MM-dd
  deliveryMethod?: string;
  status?: string; // backend enum string
  notesToCustomer?: string;
  internalNotes?: string;
  depositAmount?: number | null;
  depositDueDate?: string | null; // yyyy-MM-dd
  balanceDueDate?: string | null; // yyyy-MM-dd
  total?: number;
};

export async function createOrder(
  input: OrderCreateInput,
): Promise<Order> {
  // Build backend OrderCreate payload
  const me = await getCurrentUser();
  const toDateTime = (d?: string | null) => (d ? `${d}T00:00:00Z` : null);
  const payload: Record<string, unknown> = {
    user_id: me.id,
    due_date: toDateTime(input.dueDate),
    delivery_method: input.deliveryMethod ?? null,
    notes_to_customer: input.notesToCustomer ?? null,
    internal_notes: input.internalNotes ?? null,
    deposit_amount: input.depositAmount ?? null,
    deposit_due_date: input.depositDueDate ?? null,
    balance_due_date: input.balanceDueDate ?? null,
    status: input.status ?? 'inquiry',
    items: [],
  };
  // Some backends also accept order_date, include if provided
  const orderDt = toDateTime(input.orderDate);
  if (orderDt) payload.order_date = orderDt;

  const response = await apiClient.post<Order>('/orders/', payload);
  return response.data;
}

export async function updateOrder(
  id: string,
  order: Partial<Order>,
): Promise<Order> {
  const response = await apiClient.patch<Order>(`/orders/${id}`, order);
  return response.data;
}

export async function deleteOrder(id: string): Promise<void> {
  await apiClient.delete(`/orders/${id}`);
}
