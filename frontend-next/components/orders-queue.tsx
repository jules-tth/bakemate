'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { readStoredToken } from '@/lib/auth';
import { fetchOrdersQueue, type QueueOrder } from '@/lib/orders';
import {
  formatBakeryDateTime,
  formatMoney,
  getActionClassMeta,
  getCurrentFrontendHref,
  getDayRunningPanelTone,
  getQueueBadge,
  getSortedOrdersQueue,
  humanizeStatus,
} from '@/lib/queue-ui';
import {
  getOpsQueuePreviewRowNextStepCue,
  getOpsQueuePreviewRowPriorityCue,
  getOpsQueuePreviewRowReasonCue,
} from '@/lib/ops-preview';

export function OrdersQueue() {
  const [orders, setOrders] = useState<QueueOrder[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError(null);

      try {
        const token = readStoredToken();
        if (!token) {
          throw new Error('Missing auth token');
        }

        const nextOrders = await fetchOrdersQueue();
        setOrders(nextOrders);
      } catch (nextError) {
        setError(nextError instanceof Error ? nextError.message : 'Unable to load authenticated /orders');
      } finally {
        setIsLoading(false);
      }
    }

    void load();
  }, []);

  const sortedOrders = useMemo(() => getSortedOrdersQueue(orders), [orders]);
  const currentAppOrderBase = getCurrentFrontendHref('/orders');

  return (
    <div className="stack ops-layout">
      <section className="card stack">
        <div className="row spread start">
          <div>
            <div className="label">BM-085 queue to detail parity entry</div>
            <h1 style={{ margin: '8px 0 0' }}>Orders queue</h1>
            <p className="muted" style={{ maxWidth: 920, marginBottom: 0 }}>
              This authenticated Next `/orders` surface now hands off into a truthful first-screen Next order-detail entry.
              Queue ordering, compact exception framing, and imported payment trust cues stay aligned, while deeper order work
              still remains in the current app.
            </p>
          </div>
          <div className="row">
            <Link className="button" href="/ops">
              Back to /ops
            </Link>
            {currentAppOrderBase ? (
              <a className="button" href={currentAppOrderBase}>
                Open current app queue
              </a>
            ) : (
              <button className="button" disabled title="Set NEXT_PUBLIC_CURRENT_FRONTEND_URL to wire current app queue links">
                Open current app queue
              </button>
            )}
          </div>
        </div>
      </section>

      {error ? <section className="card error">{error}</section> : null}

      {isLoading ? <section className="card muted">Loading authenticated /orders queue…</section> : null}
      {!isLoading && !error && sortedOrders.length === 0 ? (
        <section className="card muted">No visible orders are currently available in the queue.</section>
      ) : null}

      <section className="stack">
        {sortedOrders.map((order) => {
          const queueBadge = getQueueBadge(order);
          const actionClassMeta = getActionClassMeta(order.ops_summary.action_class);
          const priorityCue = getOpsQueuePreviewRowPriorityCue(order.queue_summary.urgency_label);
          const reasonCue = getOpsQueuePreviewRowReasonCue(
            order.day_running_focus_summary.readiness_label,
            order.day_running_focus_summary.queue_reason_preview,
          );
          const nextStepCue = getOpsQueuePreviewRowNextStepCue(
            order.day_running_focus_summary.readiness_label,
            order.day_running_focus_summary.queue_next_step_preview,
          );
          const currentAppDetailHref = order.ops_summary.primary_cta_path
            ? getCurrentFrontendHref(order.ops_summary.primary_cta_path)
            : null;

          return (
            <article className="preview-row stack" key={order.id} style={{ gap: 14 }}>
              <div className="row spread start">
                <div className="stack" style={{ gap: 8 }}>
                  <div className="row" style={{ gap: 8 }}>
                    <div style={{ fontWeight: 700 }}>{order.order_number}</div>
                    <span className={`pill ${queueBadge.tone}`}>{queueBadge.label}</span>
                    <span className={`pill ${actionClassMeta.tone}`}>{actionClassMeta.label}</span>
                  </div>
                  <div className="muted">{order.customer_summary.name || order.customer_summary.email || 'No customer'}</div>
                  <div className="muted">Due {formatBakeryDateTime(order.due_date)} · {order.delivery_method || 'delivery TBD'}</div>
                </div>
                <div className="stack ops-row-side">
                  <div style={{ fontWeight: 700 }}>{formatMoney(order.total_amount)}</div>
                  <div className="muted ops-status-chip">{humanizeStatus(order.payment_status)}</div>
                  <div>
                    <span className={`pill ${priorityCue.tone}`}>{priorityCue.label}</span>
                  </div>
                  {reasonCue ? <div className="muted ops-microcue">{reasonCue}</div> : null}
                  {nextStepCue ? <div className="muted ops-microcue">{nextStepCue}</div> : null}
                </div>
              </div>

              <div className={`card tone-${getDayRunningPanelTone(order.day_running_focus_summary.readiness_label)}`}>
                <div className="label">Day-running readiness</div>
                <div style={{ fontWeight: 700, marginTop: 6 }}>{order.day_running_focus_summary.readiness_label}</div>
                <div className="muted" style={{ marginTop: 6 }}>
                  {order.day_running_focus_summary.queue_reason_preview || order.day_running_focus_summary.reason_summary}
                </div>
                {order.day_running_focus_summary.primary_blocker_label ? (
                  <div className="muted" style={{ marginTop: 8, fontSize: 12, fontWeight: 600 }}>
                    {order.day_running_focus_summary.primary_blocker_label}
                  </div>
                ) : null}
                {order.day_running_focus_summary.queue_payment_trust_preview ? (
                  <div className="trust-cue">{order.day_running_focus_summary.queue_payment_trust_preview}</div>
                ) : null}
              </div>

              <div className="card next-action-card">
                <div>
                  <div className="label">Next action</div>
                  <div style={{ fontWeight: 700, marginTop: 6 }}>{order.ops_summary.next_action}</div>
                  <div className="muted" style={{ marginTop: 6 }}>{order.ops_summary.ops_attention}</div>
                </div>
                <div className="row" style={{ justifyContent: 'space-between' }}>
                  <div className="muted" style={{ fontSize: 12 }}>
                    BM-085 adds a truthful first-screen detail entry, while deeper order work still hands off to the current app.
                  </div>
                  <div className="row">
                    <Link className="button" href={`/orders/${order.id}`}>
                      Open detail
                    </Link>
                    {currentAppDetailHref && order.ops_summary.primary_cta_label ? (
                      <a className="button primary" href={currentAppDetailHref}>
                        {order.ops_summary.primary_cta_label} in current app
                      </a>
                    ) : null}
                  </div>
                </div>
              </div>
            </article>
          );
        })}
      </section>
    </div>
  );
}
