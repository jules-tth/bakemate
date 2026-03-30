import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';

import { ordersApi } from '../api';
import type { CreateOrderPayload, DayRunningQueueSummary, DayRunningTriageFilter, OrderRecord } from '../api';
import { formatBakeryDate, formatBakeryDateOnly, formatBakeryDateTime } from '../utils/dateTime';

function getInitialForm(): CreateOrderPayload {
  return {
    due_date: '',
    delivery_method: 'pickup',
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    deposit_amount: 0,
    items: [
      {
        name: '',
        description: '',
        quantity: 1,
        unit_price: 0,
      },
    ],
  };
}

function formatMoney(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}


function humanizeStatus(value: string) {
  return value.split('_').join(' ');
}

function getQueueBadge(order: OrderRecord) {
  if (order.queue_summary.is_overdue) {
    return {
      label: 'Overdue',
      className: 'bg-rose-100 text-rose-700',
    };
  }
  if (order.queue_summary.is_due_today) {
    return {
      label: 'Due today',
      className: 'bg-amber-100 text-amber-800',
    };
  }
  if (order.queue_summary.days_until_due <= 3) {
    return {
      label: 'Next up',
      className: 'bg-sky-100 text-sky-800',
    };
  }
  return {
    label: 'Upcoming',
    className: 'bg-slate-100 text-slate-700',
  };
}

function getRiskTone(level: string) {
  if (level === 'high') {
    return 'text-rose-700';
  }
  if (level === 'medium') {
    return 'text-amber-700';
  }
  return 'text-emerald-700';
}

function getDayRunningMeta(readinessLabel: string) {
  switch (readinessLabel) {
    case 'Ready for today':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'Needs attention today':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    default:
      return 'border-rose-200 bg-rose-50 text-rose-700';
  }
}

function shouldShowDayRunningReasonPreview(readinessLabel: string) {
  return readinessLabel === 'Blocked for today' || readinessLabel === 'Needs attention today';
}

function getDayRunningFilterLabel(filter: 'all' | DayRunningTriageFilter) {
  switch (filter) {
    case 'blocked':
      return 'Blocked for today';
    case 'needs_attention':
      return 'Needs attention today';
    case 'ready':
      return 'Ready for today';
    default:
      return 'All day-running work';
  }
}

function getActionClassMeta(actionClass: string) {
  switch (actionClass) {
    case 'payment_now':
      return {
        label: 'Payment now',
        className: 'bg-rose-100 text-rose-700',
        ctaClassName: 'bg-rose-600 text-white hover:bg-rose-700',
      };
    case 'invoice_blocked':
      return {
        label: 'Invoice blocked',
        className: 'bg-violet-100 text-violet-700',
        ctaClassName: 'bg-violet-600 text-white hover:bg-violet-700',
      };
    case 'handoff_today':
      return {
        label: 'Handoff today',
        className: 'bg-amber-100 text-amber-800',
        ctaClassName: 'bg-amber-500 text-slate-950 hover:bg-amber-400',
      };
    default:
      return {
        label: 'Watch',
        className: 'bg-slate-100 text-slate-700',
        ctaClassName: 'bg-slate-900 text-white hover:bg-slate-700',
      };
  }
}

const ACTION_FILTERS = ['all', 'payment_now', 'invoice_blocked', 'handoff_today', 'watch'] as const;
const URGENCY_FILTERS = ['all', 'Urgent', 'Today', 'Next up', 'Watch'] as const;
const DAY_RUNNING_FILTERS = ['all', 'blocked', 'needs_attention', 'ready'] as const;

function getDayRunningCount(summary: DayRunningQueueSummary | null, filter: 'all' | DayRunningTriageFilter) {
  if (!summary) {
    return null;
  }

  switch (filter) {
    case 'blocked':
      return summary.blocked_count;
    case 'needs_attention':
      return summary.needs_attention_count;
    case 'ready':
      return summary.ready_count;
    default:
      return summary.all_count;
  }
}

export default function Orders() {
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [form, setForm] = useState<CreateOrderPayload>(getInitialForm);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionFilter, setActionFilter] = useState<(typeof ACTION_FILTERS)[number]>('all');
  const [urgencyFilter, setUrgencyFilter] = useState<(typeof URGENCY_FILTERS)[number]>('all');
  const [dayRunningFilter, setDayRunningFilter] = useState<(typeof DAY_RUNNING_FILTERS)[number]>('all');
  const [dayRunningSummary, setDayRunningSummary] = useState<DayRunningQueueSummary | null>(null);

  async function loadOrders(
    selectedDayRunning: (typeof DAY_RUNNING_FILTERS)[number] = dayRunningFilter,
    selectedAction: (typeof ACTION_FILTERS)[number] = actionFilter,
    selectedUrgency: (typeof URGENCY_FILTERS)[number] = urgencyFilter,
  ) {
    setIsLoading(true);
    setError(null);
    try {
      const params = {
        day_running: selectedDayRunning === 'all' ? undefined : selectedDayRunning,
        action_class: selectedAction === 'all' ? undefined : selectedAction,
        urgency: selectedUrgency === 'all' ? undefined : selectedUrgency,
      };
      const [data, summary] = await Promise.all([ordersApi.list(params), ordersApi.getDayRunningSummary(params)]);
      setOrders(data);
      setDayRunningSummary(summary);
    } catch {
      setError('Unable to load orders.');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadOrders(dayRunningFilter, actionFilter, urgencyFilter);
  }, [actionFilter, dayRunningFilter, urgencyFilter]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      const payload: CreateOrderPayload = {
        ...form,
        due_date: new Date(form.due_date).toISOString(),
        deposit_amount: form.deposit_amount || undefined,
        items: form.items.filter((item) => item.name.trim().length > 0),
      };
      await ordersApi.create(payload);
      setForm(getInitialForm());
      await loadOrders(dayRunningFilter, actionFilter, urgencyFilter);
    } catch {
      setError('Unable to save order.');
    } finally {
      setIsSaving(false);
    }
  };

  const filteredOrders = useMemo(() => {
    return [...orders].sort((left, right) => {
      const urgencyDelta = left.queue_summary.urgency_rank - right.queue_summary.urgency_rank;
      if (urgencyDelta !== 0) {
        return urgencyDelta;
      }
      return new Date(left.due_date).getTime() - new Date(right.due_date).getTime();
    });
  }, [orders]);

  const groupedOrders = useMemo(() => {
    const groups = new Map<string, OrderRecord[]>();
    for (const order of filteredOrders) {
      const key = order.queue_summary.urgency_label;
      groups.set(key, [...(groups.get(key) || []), order]);
    }
    return Array.from(groups.entries());
  }, [filteredOrders]);

  const firstItem = form.items[0];

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Orders</h1>
            <p className="mt-1 text-sm text-slate-600">
              Track customer linkage, invoice readiness, payment follow-up, and handoff urgency from one queue.
            </p>
          </div>
          <div className="rounded-xl bg-slate-100 px-4 py-3 text-right">
            <div className="text-xs uppercase tracking-wide text-slate-500">Visible orders</div>
            <div className="text-2xl font-semibold text-slate-900">{filteredOrders.length}</div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[360px,minmax(0,1fr)]">
        <form className="rounded-2xl bg-white p-6 shadow-sm" onSubmit={handleSubmit}>
          <h2 className="text-lg font-semibold text-slate-900">New order</h2>
          <div className="mt-4 space-y-4">
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Customer name"
              value={form.customer_name}
              onChange={(event) => setForm({ ...form, customer_name: event.target.value })}
            />
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Customer email"
              type="email"
              value={form.customer_email}
              onChange={(event) => setForm({ ...form, customer_email: event.target.value })}
            />
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Customer phone"
              value={form.customer_phone}
              onChange={(event) => setForm({ ...form, customer_phone: event.target.value })}
            />
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              type="datetime-local"
              required
              value={form.due_date}
              onChange={(event) => setForm({ ...form, due_date: event.target.value })}
            />
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Delivery method"
              value={form.delivery_method}
              onChange={(event) => setForm({ ...form, delivery_method: event.target.value })}
            />
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Deposit amount"
              min="0"
              step="0.01"
              type="number"
              value={form.deposit_amount || ''}
              onChange={(event) =>
                setForm({ ...form, deposit_amount: Number(event.target.value) || 0 })
              }
            />
            <div className="rounded-xl border border-slate-200 p-4">
              <div className="text-sm font-medium text-slate-700">Primary line item</div>
              <div className="mt-3 space-y-3">
                <input
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  placeholder="Item name"
                  required
                  value={firstItem.name}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      items: [{ ...firstItem, name: event.target.value }],
                    })
                  }
                />
                <input
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  placeholder="Description"
                  value={firstItem.description}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      items: [{ ...firstItem, description: event.target.value }],
                    })
                  }
                />
                <div className="grid gap-3 sm:grid-cols-2">
                  <input
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    min="1"
                    type="number"
                    value={firstItem.quantity}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        items: [{ ...firstItem, quantity: Number(event.target.value) || 1 }],
                      })
                    }
                  />
                  <input
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    min="0"
                    step="0.01"
                    type="number"
                    value={firstItem.unit_price}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        items: [{ ...firstItem, unit_price: Number(event.target.value) || 0 }],
                      })
                    }
                  />
                </div>
              </div>
            </div>
          </div>
          {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
          <button
            className="mt-5 w-full rounded-lg bg-slate-900 px-4 py-2 font-semibold text-white"
            disabled={isSaving}
            type="submit"
          >
            {isSaving ? 'Saving...' : 'Create order'}
          </button>
        </form>

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-slate-900">Ops queue</h2>
            <div className="flex flex-wrap gap-2">
              <button
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700"
                onClick={() => void loadOrders(dayRunningFilter)}
                type="button"
              >
                Refresh
              </button>
            </div>
          </div>

          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-sm font-medium text-slate-900">Day-running triage</div>
            <div className="mt-1 text-sm text-slate-600">
              Narrow the queue using the same day-running readiness story shown on each order.
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {DAY_RUNNING_FILTERS.map((value) => {
                const isActive = dayRunningFilter === value;
                return (
                  <button
                    key={value}
                    className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? 'border-slate-900 bg-slate-900 text-white'
                        : 'border-slate-300 bg-white text-slate-700 hover:border-slate-400'
                    }`}
                    onClick={() => setDayRunningFilter(value)}
                    type="button"
                  >
                    <span>{getDayRunningFilterLabel(value)}</span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                        isActive ? 'bg-white/15 text-white' : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {getDayRunningCount(dayRunningSummary, value) ?? '—'}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <label className="text-sm text-slate-700">
              <div className="mb-1 font-medium">Action class</div>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
                value={actionFilter}
                onChange={(event) =>
                  setActionFilter(event.target.value as (typeof ACTION_FILTERS)[number])
                }
              >
                {ACTION_FILTERS.map((value) => (
                  <option key={value} value={value}>
                    {value === 'all' ? 'All actions' : getActionClassMeta(value).label}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm text-slate-700">
              <div className="mb-1 font-medium">Urgency</div>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
                value={urgencyFilter}
                onChange={(event) =>
                  setUrgencyFilter(event.target.value as (typeof URGENCY_FILTERS)[number])
                }
              >
                {URGENCY_FILTERS.map((value) => (
                  <option key={value} value={value}>
                    {value === 'all' ? 'All urgency levels' : value}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {isLoading ? <p className="mt-4 text-sm text-slate-600">Loading orders...</p> : null}
          {!isLoading && filteredOrders.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">
              No orders match the {getDayRunningFilterLabel(dayRunningFilter).toLowerCase()} queue view.
            </p>
          ) : null}

          <div className="mt-6 space-y-6">
            {groupedOrders.map(([groupLabel, groupOrders]) => (
              <section key={groupLabel} className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">
                      {groupLabel}
                    </h3>
                    <p className="text-xs text-slate-500">{groupOrders.length} order(s)</p>
                  </div>
                </div>
                <div className="space-y-4">
                  {groupOrders.map((order) => {
                    const queueBadge = getQueueBadge(order);
                    const riskTone = getRiskTone(order.risk_summary.level);
                    const actionClassMeta = getActionClassMeta(order.ops_summary.action_class);
                    const dayRunningMeta = getDayRunningMeta(order.day_running_focus_summary.readiness_label);
                    return (
                      <article className="rounded-xl border border-slate-200 p-4" key={order.id}>
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-900">
                              {order.order_number} •{' '}
                              {order.customer_summary.name ||
                                order.customer_summary.email ||
                                'No customer'}
                              <span
                                className={`rounded-full px-2 py-1 text-xs font-semibold ${queueBadge.className}`}
                              >
                                {queueBadge.label}
                              </span>
                              <span
                                className={`rounded-full px-2 py-1 text-xs font-semibold ${actionClassMeta.className}`}
                              >
                                {actionClassMeta.label}
                              </span>
                            </div>
                            <div className="mt-1 text-sm text-slate-600">
                              Due {formatBakeryDateTime(order.due_date)} • {order.delivery_method || 'delivery TBD'}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-semibold text-slate-900">
                              {formatMoney(order.total_amount)}
                            </div>
                            <div className="text-xs uppercase tracking-wide text-slate-500">
                              {humanizeStatus(order.payment_status)}
                            </div>
                            <div className="mt-2 text-xs font-semibold text-slate-600">
                              {order.queue_summary.urgency_label}
                            </div>
                          </div>
                        </div>
                        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <div className="text-xs uppercase tracking-wide text-amber-700">
                                Next action
                              </div>
                              <div className="mt-1 text-base font-semibold text-slate-900">
                                {order.ops_summary.next_action}
                              </div>
                              <div className="mt-1 text-sm text-slate-700">
                                {order.ops_summary.ops_attention}
                              </div>
                            </div>
                            <Link
                              aria-label={`${order.ops_summary.primary_cta_label} for ${order.order_number}`}
                              className={`inline-flex rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${actionClassMeta.ctaClassName}`}
                              to={order.ops_summary.primary_cta_path}
                            >
                              {order.ops_summary.primary_cta_label}
                            </Link>
                          </div>
                          <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
                            <span className="rounded-full bg-white px-2 py-1 ring-1 ring-slate-200">
                              Deposit due: {formatBakeryDateOnly(order.deposit_due_date)}
                            </span>
                            <span className="rounded-full bg-white px-2 py-1 ring-1 ring-slate-200">
                              Balance due: {formatBakeryDateOnly(order.balance_due_date)}
                            </span>
                          </div>
                        </div>
                        <div className={`mt-4 rounded-xl border p-4 ${dayRunningMeta}`}>
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <div className="text-xs uppercase tracking-wide">Day-running readiness</div>
                              <div className="mt-1 text-sm font-semibold text-slate-900">
                                {order.day_running_focus_summary.readiness_label}
                              </div>
                              {shouldShowDayRunningReasonPreview(order.day_running_focus_summary.readiness_label) ? (
                                <>
                                  <div className="mt-1 text-sm text-slate-700">
                                    {order.day_running_focus_summary.queue_reason_preview ?? order.day_running_focus_summary.reason_summary}
                                  </div>
                                  {order.day_running_focus_summary.queue_next_step_preview ? (
                                    <div className="mt-1 text-xs font-medium text-slate-600">
                                      {order.day_running_focus_summary.queue_next_step_preview}
                                    </div>
                                  ) : null}
                                  {order.day_running_focus_summary.queue_contact_preview ? (
                                    <div className="mt-1 text-xs text-slate-500">
                                      {order.day_running_focus_summary.queue_contact_preview}
                                    </div>
                                  ) : null}
                                  {order.day_running_focus_summary.queue_payment_preview ? (
                                    <div className="mt-1 text-xs text-slate-500">
                                      {order.day_running_focus_summary.queue_payment_preview}
                                    </div>
                                  ) : null}
                                  {order.day_running_focus_summary.queue_handoff_preview ? (
                                    <div className="mt-1 text-xs text-slate-500">
                                      {order.day_running_focus_summary.queue_handoff_preview}
                                    </div>
                                  ) : null}
                                  {order.day_running_focus_summary.queue_production_preview ? (
                                    <div className="mt-1 text-xs text-slate-500">
                                      {order.day_running_focus_summary.queue_production_preview}
                                    </div>
                                  ) : null}
                                  {order.day_running_focus_summary.queue_invoice_preview ? (
                                    <div className="mt-1 text-xs text-slate-500">
                                      {order.day_running_focus_summary.queue_invoice_preview}
                                    </div>
                                  ) : null}
                                  {order.day_running_focus_summary.queue_review_preview ? (
                                    <div className="mt-1 text-xs text-slate-500">
                                      {order.day_running_focus_summary.queue_review_preview}
                                    </div>
                                  ) : null}
                                </>
                              ) : null}
                            </div>
                            <div className="text-right text-xs text-slate-600 max-w-[220px]">
                              {order.day_running_focus_summary.primary_blocker_label}
                            </div>
                          </div>
                        </div>
                        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <div className="text-xs uppercase tracking-wide text-slate-500">Production readiness</div>
                              <div className="mt-1 text-sm font-semibold text-slate-900">
                                {order.production_focus_summary.readiness_label}
                              </div>
                              <div className="mt-1 text-sm text-slate-600">{order.production_focus_summary.attention_note}</div>
                            </div>
                            <div className="text-right text-xs text-slate-500">
                              {order.production_focus_summary.item_count_label}
                            </div>
                          </div>
                        </div>
                        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <div className="text-xs uppercase tracking-wide text-slate-500">Contact readiness</div>
                              <div className="mt-1 text-sm font-semibold text-slate-900">
                                {order.contact_focus_summary.readiness_label}
                              </div>
                              <div className="mt-1 text-sm text-slate-600">{order.contact_focus_summary.attention_note}</div>
                            </div>
                            <div className="text-right text-xs text-slate-500 max-w-[220px]">
                              {order.contact_focus_summary.best_contact_methods_summary}
                            </div>
                          </div>
                        </div>
                        <div className="mt-4 grid gap-3 md:grid-cols-3">
                          <div className="rounded-lg bg-slate-50 p-3">
                            <div className="text-xs uppercase tracking-wide text-slate-500">Customer</div>
                            <div className="mt-1 text-sm text-slate-800">
                              {order.customer_summary.is_linked_contact ? 'Linked contact' : 'Snapshot only'}
                            </div>
                            <div className="mt-1 text-xs text-slate-600">
                              {order.customer_summary.email || order.customer_summary.phone || 'No contact details'}
                            </div>
                            <div className="mt-2 text-xs text-slate-500">
                              {order.customer_history_summary.total_orders} total orders • {order.customer_history_summary.completed_orders} completed
                            </div>
                            <div className="mt-1 text-xs text-slate-500">
                              {order.customer_history_summary.last_order_date
                                ? `Last order ${formatBakeryDate(order.customer_history_summary.last_order_date)}`
                                : 'First order on record'}
                            </div>
                          </div>
                          <div className="rounded-lg bg-slate-50 p-3">
                            <div className="text-xs uppercase tracking-wide text-slate-500">Payment</div>
                            <div className="mt-1 text-sm text-slate-800">
                              Paid {formatMoney(order.payment_summary.amount_paid)}
                            </div>
                            <div className="mt-1 text-xs text-slate-600">
                              Due {formatMoney(order.payment_summary.amount_due)}
                            </div>
                            <div className={`mt-2 text-xs font-semibold ${riskTone}`}>
                              Risk {humanizeStatus(order.risk_summary.level)}
                            </div>
                            <div className="mt-1 text-xs text-slate-600">
                              {order.risk_summary.has_overdue_payment
                                ? `Overdue money ${formatMoney(order.risk_summary.overdue_amount)}`
                                : `Outstanding money ${formatMoney(order.risk_summary.outstanding_amount)}`}
                            </div>
                          </div>
                          <div className="rounded-lg bg-slate-50 p-3">
                            <div className="text-xs uppercase tracking-wide text-slate-500">Ops</div>
                            <div className="mt-1 text-sm text-slate-800">
                              {humanizeStatus(order.invoice_summary.status)} • {humanizeStatus(order.queue_summary.due_bucket)}
                            </div>
                            <div className="mt-1 text-xs text-slate-600">
                              {order.invoice_summary.missing_fields.length > 0
                                ? order.invoice_summary.missing_fields.join(', ')
                                : 'Ready for ops handoff'}
                            </div>
                            <div className="mt-2 text-xs text-slate-500">
                              {order.queue_summary.days_until_due < 0
                                ? `${Math.abs(order.queue_summary.days_until_due)} day(s) late`
                                : `${order.queue_summary.days_until_due} day(s) to due date`}
                            </div>
                            <div className="mt-1 text-xs text-slate-500">
                              {order.risk_summary.reasons.length > 0
                                ? order.risk_summary.reasons.map(humanizeStatus).join(', ')
                                : 'No active money-risk flags'}
                            </div>
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </section>
            ))}
          </div>
        </section>
      </section>
    </div>
  );
}
