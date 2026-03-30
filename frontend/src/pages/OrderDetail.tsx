import { useEffect, useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';

import { ordersApi } from '../api';
import type { OrderRecord } from '../api';
import { formatBakeryDate, formatBakeryDateOnly, formatBakeryDateTime } from '../utils/dateTime';

const DETAIL_PANELS = ['review', 'invoice', 'payment', 'handoff'] as const;
type DetailPanel = (typeof DETAIL_PANELS)[number];

function formatMoney(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

function humanizeStatus(value: string) {
  return value.split('_').join(' ');
}

function describeImportReviewReason(reason?: OrderRecord['primary_review_reason']) {
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

function isDetailPanel(value: string | null): value is DetailPanel {
  return value !== null && DETAIL_PANELS.includes(value as DetailPanel);
}

function describeAmountOwedNow(stage: string) {
  switch (stage) {
    case 'deposit':
      return 'Current checkpoint: collect the deposit only.';
    case 'balance':
      return 'Current checkpoint: collect the final balance only.';
    case 'settled':
      return 'Nothing is owed right now.';
    default:
      return 'No payment checkpoint is set, so this falls back to the total remaining balance.';
  }
}

function getProductionReadinessTone(readinessLabel: string) {
  switch (readinessLabel) {
    case 'Ready to make':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'Needs clarification':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    default:
      return 'border-rose-200 bg-rose-50 text-rose-700';
  }
}

function getContactReadinessTone(readinessLabel: string) {
  switch (readinessLabel) {
    case 'Ready to contact':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'Limited contact info':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    default:
      return 'border-rose-200 bg-rose-50 text-rose-700';
  }
}

function getDayRunningTone(readinessLabel: string) {
  switch (readinessLabel) {
    case 'Ready for today':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'Needs attention today':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    default:
      return 'border-rose-200 bg-rose-50 text-rose-700';
  }
}

export default function OrderDetail() {
  const { orderId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [order, setOrder] = useState<OrderRecord | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadOrder() {
      if (!orderId) {
        setError('Order not found.');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const data = await ordersApi.get(orderId);
        setOrder(data);
      } catch {
        setError('Unable to load order.');
      } finally {
        setIsLoading(false);
      }
    }

    void loadOrder();
  }, [orderId]);

  const activePanel = useMemo<DetailPanel>(() => {
    const panel = searchParams.get('panel');
    if (isDetailPanel(panel)) {
      return panel;
    }
    if (order && isDetailPanel(order.ops_summary.primary_cta_panel)) {
      return order.ops_summary.primary_cta_panel;
    }
    return 'review';
  }, [order, searchParams]);

  const setActivePanel = (panel: DetailPanel) => {
    const next = new URLSearchParams(searchParams);
    next.set('panel', panel);
    setSearchParams(next, { replace: true });
  };

  const panelContent = useMemo(() => {
    if (!order) {
      return null;
    }

    switch (activePanel) {
      case 'invoice':
        return {
          eyebrow: 'Invoice detail',
          title: order.invoice_focus_summary.next_step,
          description:
            'The invoice panel is the operator surface for send-readiness, billing identity, amount context, blockers, and the next invoice move.',
          points: [
            `Status: ${humanizeStatus(order.invoice_focus_summary.status_label)}`,
            order.invoice_focus_summary.order_identity,
            order.invoice_focus_summary.amount_summary,
          ],
          accentClassName: 'border-violet-200 bg-violet-50',
        };
      case 'payment':
        return {
          eyebrow: 'Payment detail',
          title: order.payment_focus_summary.next_step,
          description:
            'The payment panel is the operator surface for what is owed now, what stage the order is in, why it is risky, and the next payment move.',
          points: [
            `Amount owed now: ${formatMoney(order.payment_focus_summary.amount_owed_now)}`,
            `State: ${order.payment_focus_summary.payment_state}`,
            order.payment_focus_summary.due_timing,
          ],
          accentClassName: 'border-rose-200 bg-rose-50',
        };
      case 'handoff':
        return {
          eyebrow: 'Handoff detail',
          title: order.handoff_focus_summary.next_step,
          description:
            'The handoff panel is the operator first screen for timing, method, contact, destination clues, and anything still missing before release.',
          points: [
            `Handoff time: ${order.handoff_focus_summary.handoff_time_label}`,
            `Method: ${order.handoff_focus_summary.method_label}`,
            `Readiness: ${order.handoff_focus_summary.readiness_note}`,
          ],
          accentClassName: 'border-amber-200 bg-amber-50',
        };
      default:
        return {
          eyebrow: 'Review detail',
          title: order.review_focus_summary.next_step,
          description:
            'The review panel is now the operator first screen for understanding what the order is, when it is due, how safe the cross-cutting basics look, and what to do next.',
          points: [
            `Order: ${order.review_focus_summary.order_number}`,
            `Status: ${order.review_focus_summary.status_label}`,
            order.review_focus_summary.due_label,
          ],
          accentClassName: 'border-slate-200 bg-slate-50',
        };
    }
  }, [activePanel, order]);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <Link className="text-sm font-medium text-slate-500 hover:text-slate-900" to="/orders">
              ← Back to orders
            </Link>
            <h1 className="mt-2 text-2xl font-bold text-slate-900">
              {order?.order_number || 'Order detail'}
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Practical operator detail view for queue triage and handoff follow-up.
            </p>
          </div>
        </div>
      </section>

      {isLoading ? <p className="text-sm text-slate-600">Loading order...</p> : null}
      {error ? <p className="text-sm text-red-600">Unable to load order.</p> : null}

      {order && panelContent ? (
        <section className="grid gap-6 lg:grid-cols-[minmax(0,2fr),minmax(320px,1fr)]">
          <div className="space-y-6">
            <article className={`rounded-2xl border p-6 shadow-sm ${panelContent.accentClassName}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {panelContent.eyebrow}
                  </div>
                  <h2 className="mt-1 text-xl font-semibold text-slate-900">{panelContent.title}</h2>
                  <p className="mt-2 text-sm text-slate-700">{panelContent.description}</p>
                </div>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">
                  CTA target: {order.ops_summary.primary_cta_panel}
                </span>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                {panelContent.points.map((point) => (
                  <div className="rounded-xl bg-white/80 p-3 text-sm text-slate-700 ring-1 ring-slate-200" key={point}>
                    {point}
                  </div>
                ))}
              </div>
            </article>

            {activePanel === 'review' ? (
              <article className="rounded-2xl bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Review working surface</h2>
                    <p className="mt-2 text-sm text-slate-600">
                      This first screen should let the operator understand the order quickly without hunting across payment, invoice, and handoff sections first.
                    </p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700 ring-1 ring-slate-200">
                    {order.queue_summary.urgency_label}
                  </span>
                </div>

                <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.2fr),minmax(0,0.8fr)]">
                  <div className="space-y-4">
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Order at a glance</div>
                      <div className="mt-2 text-2xl font-bold text-slate-900">{order.review_focus_summary.order_number}</div>
                      <div className="mt-1 text-sm font-medium text-slate-900">{order.review_focus_summary.customer_name}</div>
                      <div className="mt-2 text-sm text-slate-700">{order.review_focus_summary.due_label}</div>
                      <div className="mt-1 text-sm text-slate-600">Status: {order.review_focus_summary.status_label}</div>
                    </div>

                    <div className="rounded-xl border border-slate-200 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">What the customer is expecting</div>
                      <div className="mt-2 text-sm font-semibold text-slate-900">{order.review_focus_summary.item_summary}</div>
                      <div className="mt-1 text-sm text-slate-600">{order.review_focus_summary.item_count_label}</div>
                    </div>

                    <div className="rounded-xl border border-slate-200 p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Day-running readiness</div>
                          <div className="mt-2 text-sm font-semibold text-slate-900">{order.day_running_focus_summary.primary_blocker_label}</div>
                          <div className="mt-1 text-sm text-slate-600">{order.day_running_focus_summary.reason_summary}</div>
                        </div>
                        <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${getDayRunningTone(order.day_running_focus_summary.readiness_label)}`}>
                          {order.day_running_focus_summary.readiness_label}
                        </span>
                      </div>
                      <div className="mt-3 text-sm font-semibold text-slate-900">{order.day_running_focus_summary.next_step}</div>
                      {order.day_running_focus_summary.supporting_items.length > 0 ? (
                        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
                          {order.day_running_focus_summary.supporting_items.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      ) : null}
                    </div>

                    <div className="rounded-xl border border-slate-200 p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Production readiness</div>
                          <div className="mt-2 text-sm font-semibold text-slate-900">{order.production_focus_summary.contents_summary}</div>
                          <div className="mt-1 text-sm text-slate-600">{order.production_focus_summary.item_count_label}</div>
                        </div>
                        <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${getProductionReadinessTone(order.production_focus_summary.readiness_label)}`}>
                          {order.production_focus_summary.readiness_label}
                        </span>
                      </div>
                      <div className="mt-3 text-sm text-slate-700">{order.production_focus_summary.attention_note}</div>
                    </div>

                    <div className="rounded-xl border border-slate-200 p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Contact readiness</div>
                          <div className="mt-2 text-sm font-semibold text-slate-900">{order.contact_focus_summary.customer_display_name}</div>
                          <div className="mt-1 text-sm text-slate-600">{order.contact_focus_summary.best_contact_methods_summary}</div>
                        </div>
                        <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${getContactReadinessTone(order.contact_focus_summary.readiness_label)}`}>
                          {order.contact_focus_summary.readiness_label}
                        </span>
                      </div>
                      <div className="mt-3 text-sm text-slate-700">{order.contact_focus_summary.attention_note}</div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Payment confidence</div>
                        <div className="mt-2 text-sm text-slate-900">{order.review_focus_summary.payment_confidence}</div>
                      </div>
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Invoice confidence</div>
                        <div className="mt-2 text-sm text-slate-900">{order.review_focus_summary.invoice_confidence}</div>
                      </div>
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Handoff confidence</div>
                        <div className="mt-2 text-sm text-slate-900">{order.review_focus_summary.handoff_confidence}</div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-amber-700">Risk / attention</div>
                      <div className="mt-2 text-sm text-slate-900">{order.review_focus_summary.risk_note}</div>
                    </div>
                    <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-rose-700">Missing production basics</div>
                      {order.production_focus_summary.missing_basics.length > 0 ? (
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-900">
                          {order.production_focus_summary.missing_basics.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="mt-2 text-sm text-slate-900">No obvious production basics are missing from the current order record.</div>
                      )}
                    </div>
                    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-amber-700">Missing contact basics</div>
                      {order.contact_focus_summary.missing_basics.length > 0 ? (
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-900">
                          {order.contact_focus_summary.missing_basics.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="mt-2 text-sm text-slate-900">No obvious contact basics are missing from the current order record.</div>
                      )}
                    </div>
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Next contact step</div>
                      <div className="mt-2 text-sm font-semibold text-slate-900">{order.contact_focus_summary.next_step}</div>
                      <div className="mt-1 text-sm text-slate-700">{order.contact_focus_summary.next_step_detail}</div>
                    </div>
                  </div>
                </div>
              </article>
            ) : null}

            {activePanel === 'invoice' ? (
              <article className="rounded-2xl bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Invoice working surface</h2>
                    <p className="mt-2 text-sm text-slate-600">
                      Invoice readiness stays compact here so an operator can trust what is safe to send and what still blocks billing follow-up.
                    </p>
                  </div>
                  <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-violet-700 ring-1 ring-violet-200">
                    {humanizeStatus(order.invoice_focus_summary.status_label)}
                  </span>
                </div>

                <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.2fr),minmax(0,0.8fr)]">
                  <div className="space-y-4">
                    <div className="rounded-2xl border border-violet-100 bg-violet-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-violet-700">Readiness</div>
                      <div className="mt-2 text-2xl font-bold text-slate-900">
                        {humanizeStatus(order.invoice_focus_summary.status_label)}
                      </div>
                      <div className="mt-2 text-sm text-slate-700">{order.invoice_focus_summary.readiness_note}</div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Order identity</div>
                        <div className="mt-2 text-sm font-semibold text-slate-900">{order.invoice_focus_summary.order_identity}</div>
                        <div className="mt-1 text-sm text-slate-600">
                          Invoice status: {humanizeStatus(order.invoice_summary.status)}
                        </div>
                      </div>
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Customer identity</div>
                        <div className="mt-2 text-sm font-semibold text-slate-900">
                          {order.invoice_focus_summary.customer_identity}
                        </div>
                        <div className="mt-1 text-sm text-slate-600">
                          {order.customer_summary.is_linked_contact ? 'Linked customer contact' : 'Order-only customer snapshot'}
                        </div>
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Amount context</div>
                        <div className="mt-2 text-sm text-slate-900">{order.invoice_focus_summary.amount_summary}</div>
                      </div>
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Payment context</div>
                        <div className="mt-2 text-sm text-slate-900">{order.invoice_focus_summary.payment_context}</div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-rose-700">Invoice blockers</div>
                      {order.invoice_focus_summary.blockers.length > 0 ? (
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-900">
                          {order.invoice_focus_summary.blockers.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="mt-2 text-sm text-slate-900">No invoice blockers from the current order record.</div>
                      )}
                    </div>
                    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-amber-700">Missing basics</div>
                      {order.invoice_focus_summary.missing_basics.length > 0 ? (
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-900">
                          {order.invoice_focus_summary.missing_basics.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="mt-2 text-sm text-slate-900">No extra invoice basics are missing from the current order data.</div>
                      )}
                    </div>
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Next invoice step</div>
                      <div className="mt-2 text-sm font-semibold text-slate-900">{order.invoice_focus_summary.next_step}</div>
                      <div className="mt-1 text-sm text-slate-700">{order.invoice_focus_summary.next_step_detail}</div>
                    </div>
                  </div>
                </div>
              </article>
            ) : null}

            {activePanel === 'payment' ? (
              <article className="rounded-2xl bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Payment working surface</h2>
                    <p className="mt-2 text-sm text-slate-600">
                      Payment context stays action-native here so the operator does not need to cross-reference the queue card.
                    </p>
                  </div>
                  <span className="rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-rose-700 ring-1 ring-rose-200">
                    {order.payment_focus_summary.collection_stage}
                  </span>
                </div>

                <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.2fr),minmax(0,0.8fr)]">
                  <div className="space-y-4">
                    <div className="rounded-2xl border border-rose-100 bg-rose-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-rose-700">Amount owed now</div>
                      <div className="mt-2 text-3xl font-bold text-slate-900">
                        {formatMoney(order.payment_focus_summary.amount_owed_now)}
                      </div>
                      <div className="mt-2 text-sm text-slate-700">{order.payment_focus_summary.payment_state}</div>
                      <div className="mt-1 text-xs text-slate-600">
                        {describeAmountOwedNow(order.payment_focus_summary.collection_stage)}
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Deposit status</div>
                        <div className="mt-2 text-sm text-slate-900">{order.payment_focus_summary.deposit_status}</div>
                      </div>
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Balance status</div>
                        <div className="mt-2 text-sm text-slate-900">{order.payment_focus_summary.balance_status}</div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="rounded-xl border border-slate-200 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Due timing</div>
                      <div className="mt-2 text-sm text-slate-900">{order.payment_focus_summary.due_timing}</div>
                    </div>
                    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-amber-700">Why this order is at risk</div>
                      <div className="mt-2 text-sm text-slate-900">{order.payment_focus_summary.risk_note}</div>
                    </div>
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Next payment step</div>
                      <div className="mt-2 text-sm font-semibold text-slate-900">{order.payment_focus_summary.next_step}</div>
                      <div className="mt-1 text-sm text-slate-700">{order.payment_focus_summary.next_step_detail}</div>
                    </div>
                  </div>
                </div>
              </article>
            ) : null}

            {activePanel === 'handoff' ? (
              <article className="rounded-2xl bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Handoff working surface</h2>
                    <p className="mt-2 text-sm text-slate-600">
                      The operator should be able to prep pickup or delivery from this first screen without scanning the rest of the order.
                    </p>
                  </div>
                  <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-700 ring-1 ring-amber-200">
                    {order.handoff_focus_summary.method_status}
                  </span>
                </div>

                <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.2fr),minmax(0,0.8fr)]">
                  <div className="space-y-4">
                    <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-amber-700">Leaving when</div>
                      <div className="mt-2 text-2xl font-bold text-slate-900">
                        {order.handoff_focus_summary.handoff_time_label}
                      </div>
                      <div className="mt-2 text-sm text-slate-700">{order.handoff_focus_summary.method_label}</div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Customer contact</div>
                        <div className="mt-2 text-sm font-semibold text-slate-900">
                          {order.handoff_focus_summary.contact_name || 'Customer contact'}
                        </div>
                        <div className="mt-1 text-sm text-slate-700">{order.handoff_focus_summary.primary_contact}</div>
                        {order.handoff_focus_summary.secondary_contact ? (
                          <div className="mt-1 text-sm text-slate-600">{order.handoff_focus_summary.secondary_contact}</div>
                        ) : null}
                      </div>
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Destination clue</div>
                        <div className="mt-2 text-sm font-semibold text-slate-900">
                          {order.handoff_focus_summary.destination_label}
                        </div>
                        <div className="mt-1 text-sm text-slate-700">{order.handoff_focus_summary.destination_detail}</div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="rounded-xl border border-slate-200 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Readiness</div>
                      <div className="mt-2 text-sm text-slate-900">{order.handoff_focus_summary.readiness_note}</div>
                    </div>
                    <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-rose-700">Missing handoff basics</div>
                      {order.handoff_focus_summary.missing_basics.length > 0 ? (
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-900">
                          {order.handoff_focus_summary.missing_basics.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="mt-2 text-sm text-slate-900">No obvious handoff blockers from the current order data.</div>
                      )}
                    </div>
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Next handoff step</div>
                      <div className="mt-2 text-sm font-semibold text-slate-900">{order.handoff_focus_summary.next_step}</div>
                      <div className="mt-1 text-sm text-slate-700">{order.handoff_focus_summary.next_step_detail}</div>
                    </div>
                  </div>
                </div>
              </article>
            ) : null}

            <article className="rounded-2xl bg-white p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-lg font-semibold text-slate-900">Action panels</h2>
                <div className="flex flex-wrap gap-2">
                  {DETAIL_PANELS.map((panel) => {
                    const isActive = panel === activePanel;
                    return (
                      <button
                        className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                          isActive
                            ? 'bg-slate-900 text-white'
                            : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                        }`}
                        key={panel}
                        onClick={() => setActivePanel(panel)}
                        type="button"
                      >
                        {panel === 'review' ? 'Review' : panel.charAt(0).toUpperCase() + panel.slice(1)}
                      </button>
                    );
                  })}
                </div>
              </div>
              <p className="mt-3 text-sm text-slate-600">
                The queue CTA deep-links into one of these views so the first screen matches the promised action.
              </p>
            </article>

            <article className="rounded-2xl bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Order summary</h2>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Customer</div>
                  <div className="mt-1 text-sm text-slate-900">
                    {order.customer_summary.name || order.customer_summary.email || 'No customer'}
                  </div>
                  <div className="mt-1 text-sm text-slate-600">
                    {order.customer_summary.email || order.customer_summary.phone || 'No contact details'}
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Due</div>
                  <div className="mt-1 text-sm text-slate-900">{formatBakeryDateTime(order.due_date)}</div>
                  <div className="mt-1 text-sm text-slate-600">
                    {order.delivery_method || 'Delivery method TBD'}
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Totals</div>
                  <div className="mt-1 text-sm text-slate-900">{formatMoney(order.total_amount)}</div>
                  <div className="mt-1 text-sm text-slate-600">
                    Balance due {formatMoney(order.payment_summary.amount_due)}
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Queue</div>
                  <div className="mt-1 text-sm text-slate-900">{order.ops_summary.next_action}</div>
                  <div className="mt-1 text-sm text-slate-600">{order.ops_summary.ops_attention}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Import metadata</div>
                  <div className="mt-1 text-sm text-slate-900">
                    {order.is_imported ? (order.import_source || 'Imported record') : 'Native BakeMate record'}
                  </div>
                  <div className="mt-1 text-sm text-slate-600">
                    {order.legacy_status_raw
                      ? `Legacy status preserved as ${order.legacy_status_raw}`
                      : 'No legacy status clue available'}
                  </div>
                </div>
              </div>
            </article>

            {order.is_imported ? (
              <article className="rounded-2xl bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Imported review</h2>
                    <p className="mt-2 text-sm text-slate-600">
                      Conservative review cues derived from the same backend checks that drive the imported review filter.
                    </p>
                  </div>
                  <span className="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-sky-700 ring-1 ring-sky-200">
                    {describeImportReviewReason(order.primary_review_reason)}
                  </span>
                </div>

                <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1.2fr),minmax(0,0.8fr)]">
                  <div>
                    <div className="text-xs uppercase tracking-wide text-slate-500">Review reasons</div>
                    {order.review_reasons.length > 0 ? (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {order.review_reasons.map((reason) => (
                          <span
                            className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700"
                            key={reason}
                          >
                            {describeImportReviewReason(reason)}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <div className="mt-2 text-sm text-slate-900">No conservative review flags on this import.</div>
                    )}
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Next check</div>
                    <div className="mt-2 text-sm text-slate-900">
                      {order.review_next_check || 'No extra review step suggested from the current import signals.'}
                    </div>
                  </div>
                </div>
              </article>
            ) : null}

            <article className="rounded-2xl bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Recent customer history</h2>
              <p className="mt-2 text-sm text-slate-600">
                Compact same-customer context for import review and quick chronology checks.
              </p>

              {order.recent_customer_orders.length > 0 ? (
                <div className="mt-4 space-y-3">
                  {order.recent_customer_orders.map((historyOrder) => (
                    <Link
                      className="block rounded-xl border border-slate-200 p-4 hover:bg-slate-50"
                      key={historyOrder.id}
                      to={`/orders/${historyOrder.id}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-slate-900">{historyOrder.order_number}</div>
                          <div className="mt-1 text-xs text-slate-600">
                            Ordered {formatBakeryDateOnly(historyOrder.order_date)} • Due {formatBakeryDate(historyOrder.due_date)}
                          </div>
                          <div className="mt-1 text-xs uppercase tracking-wide text-slate-500">
                            {humanizeStatus(historyOrder.status)} • {humanizeStatus(historyOrder.payment_status)}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-semibold text-slate-900">{formatMoney(historyOrder.total_amount)}</div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-600">No recent same-customer orders are available for this record.</p>
              )}
            </article>

            <article className="rounded-2xl bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Items</h2>
              <div className="mt-4 space-y-3">
                {order.items.map((item) => (
                  <div className="rounded-xl border border-slate-200 p-4" key={item.id}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-medium text-slate-900">{item.name}</div>
                        <div className="mt-1 text-sm text-slate-600">
                          {item.description || 'No description'}
                        </div>
                      </div>
                      <div className="text-right text-sm text-slate-700">
                        <div>
                          {item.quantity} × {formatMoney(item.unit_price)}
                        </div>
                        <div className="mt-1 font-semibold text-slate-900">{formatMoney(item.total_price)}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <aside className="space-y-6">
            <article className="rounded-2xl bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Ops snapshot</h2>
              <div className="mt-4 space-y-3 text-sm text-slate-700">
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Action class</div>
                  <div className="mt-1">{order.ops_summary.action_class}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Primary CTA</div>
                  <div className="mt-1">{order.ops_summary.primary_cta_label}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Invoice</div>
                  <div className="mt-1">{order.invoice_summary.status}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Risk</div>
                  <div className="mt-1">{order.risk_summary.level}</div>
                </div>
              </div>
            </article>
          </aside>
        </section>
      ) : null}
    </div>
  );
}
