import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { ordersApi } from '../api';
import type { ImportedOrderQueueSummary, ImportedReviewReason, OrderRecord } from '../api';

type SortKey = 'priority' | 'recent_activity' | 'due_date' | 'payment_risk';
type ReviewStateFilter = 'all' | 'needs_review' | 'ready';

const REVIEW_REASON_OPTIONS: Array<{ value: ImportedReviewReason; label: string }> = [
  { value: 'overdue_payment_risk', label: 'Overdue payment risk' },
  { value: 'invoice_missing_fields', label: 'Invoice details missing' },
  { value: 'missing_contact_details', label: 'Missing contact details' },
  { value: 'unlinked_contact', label: 'Unlinked customer contact' },
];

function formatMoney(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

function formatDate(value?: string | null) {
  if (!value) {
    return 'Not set';
  }
  return new Date(value).toLocaleDateString();
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return 'Not set';
  }
  return new Date(value).toLocaleString();
}

function humanizeStatus(value: string) {
  return value.split('_').join(' ');
}

function describeReviewReason(reason?: OrderRecord['primary_review_reason']) {
  switch (reason) {
    case 'overdue_payment_risk':
      return 'Overdue payment risk';
    case 'invoice_missing_fields':
      return 'Invoice details missing';
    case 'missing_contact_details':
      return 'Missing contact details';
    case 'unlinked_contact':
      return 'Unlinked customer contact';
    default:
      return 'No review reason';
  }
}

function getVerificationChips(order: OrderRecord) {
  const chips: Array<{ label: string; className: string }> = [];

  if (order.is_imported) {
    chips.push({ label: 'Imported', className: 'bg-sky-100 text-sky-800' });
  }

  if (order.legacy_status_raw) {
    chips.push({
      label: `Legacy status ${order.legacy_status_raw}`,
      className: 'bg-indigo-100 text-indigo-800',
    });
  }

  if (order.customer_summary.is_linked_contact) {
    chips.push({ label: 'Linked contact', className: 'bg-emerald-100 text-emerald-800' });
  } else {
    chips.push({ label: 'Snapshot only', className: 'bg-amber-100 text-amber-800' });
  }

  order.review_reasons.forEach((reason) => {
    if (reason === 'missing_contact_details') {
      chips.push({ label: 'Missing contact details', className: 'bg-rose-100 text-rose-700' });
    }
    if (reason === 'invoice_missing_fields') {
      chips.push({
        label: `Invoice gaps: ${order.invoice_summary.missing_fields.length}`,
        className: 'bg-violet-100 text-violet-800',
      });
    }
    if (reason === 'overdue_payment_risk') {
      chips.push({ label: 'Overdue payment', className: 'bg-rose-100 text-rose-700' });
    }
    if (reason === 'unlinked_contact') {
      chips.push({ label: 'Needs contact match', className: 'bg-amber-100 text-amber-800' });
    }
  });

  return chips;
}

function sortOrders(orders: OrderRecord[], sortKey: SortKey) {
  if (sortKey === 'priority') {
    return orders;
  }

  const sorted = [...orders];
  sorted.sort((left, right) => {
    if (sortKey === 'payment_risk') {
      return (
        right.risk_summary.overdue_amount - left.risk_summary.overdue_amount
        || right.payment_summary.amount_due - left.payment_summary.amount_due
        || new Date(right.order_date).getTime() - new Date(left.order_date).getTime()
      );
    }

    if (sortKey === 'due_date') {
      return new Date(left.due_date).getTime() - new Date(right.due_date).getTime();
    }

    return new Date(right.order_date).getTime() - new Date(left.order_date).getTime();
  });
  return sorted;
}

export default function ImportedRecords() {
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [search, setSearch] = useState('');
  const [reviewState, setReviewState] = useState<ReviewStateFilter>('all');
  const [reviewReason, setReviewReason] = useState<ImportedReviewReason | ''>('');
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('priority');
  const [queueSummary, setQueueSummary] = useState<ImportedOrderQueueSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadOrders() {
      setIsLoading(true);
      setError(null);
      try {
        const needsReview = reviewState === 'all'
          ? undefined
          : reviewState === 'needs_review';
        const query = search.trim() || undefined;
        const [data, summary] = await Promise.all([
          ordersApi.list({
            imported_only: true,
            search: query,
            needs_review: needsReview,
            review_reason: reviewReason || undefined,
          }),
          ordersApi.getImportedSummary(query),
        ]);
        setOrders(data);
        setQueueSummary(summary);
        setSelectedOrderId((current) => {
          if (current && data.some((order) => order.id === current)) {
            return current;
          }
          return data[0]?.id || null;
        });
      } catch {
        setError('Unable to load imported records.');
      } finally {
        setIsLoading(false);
      }
    }

    void loadOrders();
  }, [reviewReason, reviewState, search]);

  useEffect(() => {
    if (reviewReason) {
      setReviewState('needs_review');
    }
  }, [reviewReason]);

  const visibleOrders = useMemo(() => sortOrders(orders, sortKey), [orders, sortKey]);

  const selectedOrder = useMemo(() => {
    if (selectedOrderId) {
      return visibleOrders.find((order) => order.id === selectedOrderId) || null;
    }
    return visibleOrders[0] || null;
  }, [selectedOrderId, visibleOrders]);

  const summary = useMemo(() => ({
    importedCount: queueSummary?.all_imported_count ?? 0,
    needsReviewCount: queueSummary?.needs_review_count ?? 0,
    noCurrentReviewCount: queueSummary?.no_current_review_count ?? 0,
    activeReasonCount: reviewReason ? queueSummary?.review_reason_counts[reviewReason] ?? 0 : null,
  }), [queueSummary, reviewReason]);

  const activeReviewReasonLabel = reviewReason
    ? REVIEW_REASON_OPTIONS.find((option) => option.value === reviewReason)?.label ?? 'Selected reason'
    : null;

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Imported records review</h1>
            <p className="mt-1 max-w-3xl text-sm text-slate-600">
              Browse imported customer orders, search by customer or order text, and sanity-check a few nearby sibling orders without rebuilding legacy logic in the browser.
            </p>
          </div>
          <div className="rounded-xl bg-slate-100 px-4 py-3 text-right">
            <div className="text-xs uppercase tracking-wide text-slate-500">Imported orders</div>
            <div className="text-2xl font-semibold text-slate-900">{summary.importedCount}</div>
          </div>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-4">
          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-500">All imported</div>
            <div className="mt-2 text-2xl font-semibold text-slate-900">{summary.importedCount}</div>
            <div className="mt-1 text-sm text-slate-600">Current imported queue size for this search.</div>
          </div>
          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-500">Needs review</div>
            <div className="mt-2 text-2xl font-semibold text-slate-900">{summary.needsReviewCount}</div>
            <div className="mt-1 text-sm text-slate-600">Conservative filter: contact gaps, invoice gaps, or overdue payment risk.</div>
          </div>
          <div className="rounded-xl border border-slate-200 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-500">No current review</div>
            <div className="mt-2 text-2xl font-semibold text-slate-900">{summary.noCurrentReviewCount}</div>
            <div className="mt-1 text-sm text-slate-600">Imported rows with no current BM-023 review flags.</div>
          </div>
          <div className="rounded-xl border border-sky-200 bg-sky-50 p-4">
            <div className="text-xs uppercase tracking-wide text-sky-700">Reason slice</div>
            <div className="mt-2 text-sm font-semibold text-slate-900">
              {activeReviewReasonLabel || 'Choose a review reason'}
            </div>
            <div className="mt-1 text-sm text-slate-700">
              {activeReviewReasonLabel
                ? `${summary.activeReasonCount ?? 0} imported records currently match this reason.`
                : 'Counts derive from the existing BM-023 review vocabulary only.'}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr),minmax(320px,0.9fr)]">
        <div className="space-y-6">
          <section className="rounded-2xl bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-end gap-3">
              <label className="min-w-[260px] flex-1 text-sm text-slate-700">
                <div className="mb-1 font-medium">Search imported records</div>
                <input
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  placeholder="Order number, customer, email, phone, delivery, or legacy text"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>
              <label className="w-full text-sm text-slate-700 md:max-w-xs">
                <div className="mb-1 font-medium">Review reason</div>
                <select
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  onChange={(event) => setReviewReason(event.target.value as ImportedReviewReason | '')}
                  value={reviewReason}
                >
                  <option value="">All reasons</option>
                  {REVIEW_REASON_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="w-full text-sm text-slate-700 md:max-w-xs">
                <div className="mb-1 font-medium">Sort</div>
                <select
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  value={sortKey}
                  onChange={(event) => setSortKey(event.target.value as SortKey)}
                >
                  <option value="priority">Imported review priority</option>
                  <option value="recent_activity">Recent activity</option>
                  <option value="due_date">Due date</option>
                  <option value="payment_risk">Payment risk</option>
                </select>
              </label>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {[
                { value: 'all' as const, label: `All imported (${summary.importedCount})` },
                { value: 'needs_review' as const, label: `Needs review (${summary.needsReviewCount})` },
                { value: 'ready' as const, label: `Ready to inspect (${summary.noCurrentReviewCount})` },
              ].map((option) => (
                <button
                  className={`rounded-full px-3 py-2 text-sm font-medium transition-colors ${
                    reviewState === option.value
                      ? 'bg-slate-900 text-white'
                      : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                  }`}
                  key={option.value}
                  onClick={() => setReviewState(option.value)}
                  type="button"
                >
                  {option.label}
                </button>
              ))}
            </div>

            {isLoading ? <p className="mt-4 text-sm text-slate-600">Loading imported records...</p> : null}
            {error ? <p className="mt-4 text-sm text-rose-600">{error}</p> : null}
            {!isLoading && !error && visibleOrders.length === 0 ? (
              <p className="mt-4 text-sm text-slate-600">No imported records match this view.</p>
            ) : null}

            <div className="mt-6 space-y-4">
              {visibleOrders.map((order) => {
                const chips = getVerificationChips(order);
                const isSelected = selectedOrder?.id === order.id;

                return (
                  <article
                    className={`rounded-2xl border p-4 transition-colors ${
                      isSelected ? 'border-slate-900 bg-slate-50' : 'border-slate-200 bg-white'
                    }`}
                    key={order.id}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-900">
                          <button
                            className="rounded-md px-0 py-0 text-left font-semibold text-slate-900 hover:text-slate-700"
                            onClick={() => setSelectedOrderId(order.id)}
                            type="button"
                          >
                            {order.order_number}
                          </button>
                          <span className="text-slate-400">•</span>
                          <span>{order.customer_summary.name || order.customer_name || 'Unknown customer'}</span>
                        </div>
                        <div className="mt-1 text-sm text-slate-600">
                          Ordered {formatDate(order.order_date)} • Due {formatDateTime(order.due_date)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold text-slate-900">{formatMoney(order.total_amount)}</div>
                        <div className="mt-1 text-xs uppercase tracking-wide text-slate-500">
                          {humanizeStatus(order.status)} • {humanizeStatus(order.payment_status)}
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2">
                      <span className="rounded-full bg-slate-900 px-2.5 py-1 text-xs font-semibold text-white">
                        {order.imported_priority_label || 'Ready after review pile'}
                      </span>
                      {chips.map((chip) => (
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${chip.className}`} key={chip.label}>
                          {chip.label}
                        </span>
                      ))}
                    </div>

                    <div className="mt-4 grid gap-3 lg:grid-cols-3">
                      <div className="rounded-xl bg-slate-50 p-3">
                        <div className="text-xs uppercase tracking-wide text-slate-500">Import source</div>
                        <div className="mt-1 text-sm text-slate-900">{order.import_source || 'Not marked as imported'}</div>
                        <div className="mt-1 text-xs text-slate-600">
                          {order.legacy_status_raw
                            ? `Preserved legacy status: ${order.legacy_status_raw}`
                            : 'No preserved legacy status clue'}
                        </div>
                      </div>
                      <div className="rounded-xl bg-slate-50 p-3">
                        <div className="text-xs uppercase tracking-wide text-slate-500">Customer history</div>
                        <div className="mt-1 text-sm text-slate-900">
                          {order.customer_history_summary.total_orders} total orders • {order.customer_history_summary.completed_orders} completed
                        </div>
                        <div className="mt-1 text-xs text-slate-600">
                          {order.customer_history_summary.last_order_date
                            ? `Last earlier order ${formatDate(order.customer_history_summary.last_order_date)}`
                            : 'No earlier order on file'}
                        </div>
                      </div>
                      <div className="rounded-xl bg-slate-50 p-3">
                        <div className="text-xs uppercase tracking-wide text-slate-500">Priority</div>
                        <div className="mt-1 text-sm font-semibold text-slate-900">
                          {order.imported_priority_label || 'Ready after review pile'}
                        </div>
                        <div className="mt-1 text-xs text-slate-600">
                          {order.review_reasons.length > 0
                            ? `${describeReviewReason(order.primary_review_reason)} leads this imported review card.`
                            : 'No conservative review flags on this import, so it stays behind the review-needed pile.'}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <Link
                        className="inline-flex rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-700"
                        to={order.ops_summary.primary_cta_path}
                      >
                        {order.ops_summary.primary_cta_label}
                      </Link>
                      <button
                        className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        onClick={() => setSelectedOrderId(order.id)}
                        type="button"
                      >
                        Inspect customer history
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        </div>

        <aside className="space-y-6">
          <section className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Recent customer history</h2>
            <p className="mt-2 text-sm text-slate-600">
              Compact same-customer context from the backend so imported orders can be sanity-checked without browser-side reconstruction.
            </p>

            {selectedOrder ? (
              <div className="mt-4 space-y-4">
                <div>
                  <div className="text-base font-semibold text-slate-900">
                    {selectedOrder.customer_summary.name || selectedOrder.customer_name || 'Unknown customer'}
                  </div>
                  <div className="mt-1 text-sm text-slate-600">
                    {selectedOrder.customer_summary.email || selectedOrder.customer_summary.phone || 'No primary contact detail on file'}
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-xs uppercase tracking-wide text-slate-500">History footprint</div>
                    <div className="mt-1 text-sm text-slate-900">{selectedOrder.customer_history_summary.total_orders} total orders</div>
                    <div className="mt-1 text-xs text-slate-600">
                      {selectedOrder.customer_history_summary.completed_orders} completed • {selectedOrder.customer_history_summary.active_orders} active
                    </div>
                  </div>
                  <div className="rounded-xl border border-slate-200 p-3">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Current imported record</div>
                    <div className="mt-1 text-sm text-slate-900">{selectedOrder.order_number}</div>
                    <div className="mt-1 text-xs text-slate-600">
                      {selectedOrder.legacy_status_raw
                        ? `Legacy status ${selectedOrder.legacy_status_raw}`
                        : 'No preserved legacy status clue'}
                    </div>
                  </div>
                </div>

                {selectedOrder.recent_customer_orders.length > 0 ? (
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recent sibling orders</div>
                    <div className="mt-3 space-y-3">
                      {selectedOrder.recent_customer_orders.map((order) => (
                        <Link
                          className="block rounded-xl border border-slate-200 p-3 hover:bg-slate-50"
                          key={order.id}
                          to={`/orders/${order.id}`}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <div className="text-sm font-semibold text-slate-900">{order.order_number}</div>
                              <div className="mt-1 text-xs text-slate-600">
                                Ordered {formatDate(order.order_date)} • Due {formatDate(order.due_date)}
                              </div>
                              <div className="mt-1 text-xs uppercase tracking-wide text-slate-500">
                                {humanizeStatus(order.status)} • {humanizeStatus(order.payment_status)}
                              </div>
                            </div>
                            <div className="text-xs font-semibold text-slate-700">{formatMoney(order.total_amount)}</div>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-slate-600">No nearby same-customer orders are available for this record yet.</p>
                )}
              </div>
            ) : (
              <p className="mt-4 text-sm text-slate-600">Pick an imported record to inspect recent same-customer history.</p>
            )}
          </section>
        </aside>
      </section>
    </div>
  );
}
