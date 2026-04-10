'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { readStoredToken } from '@/lib/auth';
import { fetchDayRunningSummary, fetchOpsPreviewOrders, type DayRunningSummary, type OpsPreviewOrder } from '@/lib/ops';
import {
  getOpsQueuePreviewDrillInAffordanceLabel,
  getOpsQueuePreviewPriorityLabel,
  getOpsQueuePreviewRowNextStepCue,
  getOpsQueuePreviewRowPriorityCue,
  getOpsQueuePreviewRowReasonCue,
  getOpsQueuePreviewScopeLabel,
} from '@/lib/ops-preview';
import {
  formatBakeryDateTime,
  formatMoney,
  getActionClassMeta,
  getCurrentFrontendHref,
  getDayRunningPanelTone,
  getQueueBadge,
  humanizeStatus,
} from '@/lib/queue-ui';

function getSummaryCards(summary: DayRunningSummary | null) {
  return [
    ['Visible day-running work', summary?.all_count ?? '—'],
    ['Blocked for today', summary?.blocked_count ?? '—'],
    ['Needs attention', summary?.needs_attention_count ?? '—'],
    ['Ready now', summary?.ready_count ?? '—'],
  ];
}


function getAttentionHeadline(summary: DayRunningSummary | null) {
  if (!summary) {
    return 'Loading today’s ops view…';
  }

  if (summary.blocked_count > 0) {
    return `${summary.blocked_count} blocked ${summary.blocked_count === 1 ? 'order needs' : 'orders need'} help first.`;
  }

  if (summary.needs_attention_count > 0) {
    return `${summary.needs_attention_count} ${summary.needs_attention_count === 1 ? 'order needs' : 'orders need'} attention next.`;
  }

  if (summary.ready_count > 0) {
    return `${summary.ready_count} ${summary.ready_count === 1 ? 'order is' : 'orders are'} ready to work now.`;
  }

  return 'No day-running work is currently visible in this preview.';
}

function getTopAttentionOrders(orders: OpsPreviewOrder[]) {
  return [...orders]
    .sort((left, right) => {
      const urgencyDelta = left.queue_summary.urgency_rank - right.queue_summary.urgency_rank;
      if (urgencyDelta !== 0) {
        return urgencyDelta;
      }

      return new Date(left.due_date).getTime() - new Date(right.due_date).getTime();
    })
    .slice(0, 6);
}

export function OpsShellProof() {
  const [summary, setSummary] = useState<DayRunningSummary | null>(null);
  const [orders, setOrders] = useState<OpsPreviewOrder[]>([]);
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

        const [nextSummary, nextOrders] = await Promise.all([fetchDayRunningSummary(), fetchOpsPreviewOrders()]);
        setSummary(nextSummary);
        setOrders(nextOrders);
      } catch (nextError) {
        setError(nextError instanceof Error ? nextError.message : 'Unable to load authenticated /ops');
      } finally {
        setIsLoading(false);
      }
    }

    void load();
  }, []);

  const summaryCards = useMemo(() => getSummaryCards(summary), [summary]);
  const topOrders = useMemo(() => getTopAttentionOrders(orders), [orders]);
  const blockedOrders = useMemo(
    () => topOrders.filter((order) => order.day_running_focus_summary.readiness_label === 'Blocked for today').slice(0, 3),
    [topOrders],
  );
  const attentionOrders = useMemo(
    () => topOrders.filter((order) => order.day_running_focus_summary.readiness_label === 'Needs attention today').slice(0, 3),
    [topOrders],
  );
  const importedReviewHref = getCurrentFrontendHref('/orders/imported');

  return (
    <div className="stack ops-layout">
      <section className="card stack">
        <div className="row spread start">
          <div>
            <div className="label">Preview</div>
            <h1 style={{ margin: '8px 0 0' }}>Ops Home</h1>
            <p className="muted" style={{ maxWidth: 860, marginBottom: 0 }}>
              A visible front door for BakeMate’s trusted day-running view. This parity-first Next.js slice preserves
              the accepted `/ops` structure and meaning and now hands off into a real Next `/orders` queue, while still leaving order detail in the current app.
            </p>
          </div>
          <div className="row">
            <Link className="button" href="/orders">
              View full queue
            </Link>
            {importedReviewHref ? (
              <a className="button primary" href={importedReviewHref}>
                Imported review
              </a>
            ) : (
              <button className="button primary" disabled title="Set NEXT_PUBLIC_CURRENT_FRONTEND_URL to wire the current app route">
                Imported review
              </button>
            )}
          </div>
        </div>
      </section>

      {error ? <section className="card error">{error}</section> : null}

      <section className="grid cols-4">
        {summaryCards.map(([label, value]) => (
          <article className="card summary-card" key={String(label)}>
            <div className="label">{label}</div>
            <div className="value">{isLoading ? '…' : value}</div>
          </article>
        ))}
      </section>

      <section className="ops-main-grid">
        <section className="card stack">
          <div className="row spread start">
            <div>
              <h2 style={{ margin: 0 }}>What needs attention now</h2>
              <p className="muted" style={{ margin: '6px 0 0' }}>{getAttentionHeadline(summary)}</p>
            </div>
            <div className="card queue-preview-card">
              <div className="label">Queue preview</div>
              <div className="value" style={{ fontSize: 24 }}>{topOrders.length}</div>
              <div className="muted queue-preview-meta">{getOpsQueuePreviewPriorityLabel()}</div>
              <div className="muted queue-preview-meta">{getOpsQueuePreviewScopeLabel(topOrders.length)}</div>
              <div className="muted queue-preview-meta">{getOpsQueuePreviewDrillInAffordanceLabel()}</div>
            </div>
          </div>

          {isLoading ? <div className="muted">Loading authenticated /ops preview…</div> : null}
          {!isLoading && !error && topOrders.length === 0 ? (
            <div className="muted">No visible ops work is currently available.</div>
          ) : null}

          <div className="stack">
            {topOrders.map((order) => {
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
                    {order.ops_summary.primary_cta_path ? (
                      <div className="muted" style={{ fontSize: 12 }}>
                        Current app CTA preserved: <code>{order.ops_summary.primary_cta_label}</code> via{' '}
                        <code>{order.ops_summary.primary_cta_path}</code>
                      </div>
                    ) : null}
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <aside className="stack">
          <section className="card stack">
            <h2 style={{ margin: 0 }}>Ops readout</h2>
            <div className="card readout-card">
              <div className="label">Blocked first</div>
              <div style={{ marginTop: 8 }}>
                {blockedOrders.length > 0
                  ? blockedOrders.map((order) => order.order_number).join(', ')
                  : 'No blocked orders in the current queue preview.'}
              </div>
            </div>
            <div className="card readout-card">
              <div className="label">Attention next</div>
              <div style={{ marginTop: 8 }}>
                {attentionOrders.length > 0
                  ? attentionOrders.map((order) => order.order_number).join(', ')
                  : 'No needs-attention orders in the current queue preview.'}
              </div>
            </div>
            <div className="card readout-card trust-readout">
              <div className="label">Imported payment trust</div>
              <div style={{ marginTop: 8 }}>
                Imported orders keep the accepted payment trust boundary visible here as
                <strong> Payment trust: legacy-limited</strong>.
              </div>
              <div className="muted" style={{ marginTop: 8, fontSize: 12 }}>
                This preview stays informational only. It does not invent stronger historical payment certainty.
              </div>
            </div>
            <div className="muted" style={{ fontSize: 12 }}>
              BM-083 preserves the current `/ops` front-door meaning while keeping non-`/ops` routes in the current app.
            </div>
            <div className="muted" style={{ fontSize: 12 }}>
              {getCurrentFrontendHref('/orders') ? (
                <>Current app detail handoff is still available via <code>NEXT_PUBLIC_CURRENT_FRONTEND_URL</code>.</>
              ) : (
                <>Set <code>NEXT_PUBLIC_CURRENT_FRONTEND_URL</code> to turn non-migrated order-detail CTAs into real current-app handoff links.</>
              )}
            </div>
          </section>
        </aside>
      </section>
    </div>
  );
}
