import { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

import { ordersApi } from '../api';
import type { DayRunningQueueSummary, DayRunningTriageFilter, OrderRecord } from '../api';
import { formatBakeryDateTime } from '../utils/dateTime';
import {
  dismissGuardedOpsRetryFeedback,
  getGuardedOpsRetryFeedback,
  getGuardedOpsRetryUiState,
} from './opsHomeRetryState';
import { getOpsQueuePreviewDrillInAffordanceLabel } from './opsQueuePreviewDrillInAffordance';
import { getOpsQueuePreviewPriorityLabel } from './opsQueuePreviewPriority';
import { getOpsQueuePreviewRowNextStepCue } from './opsQueuePreviewRowNextStepCue';
import { getOpsQueuePreviewRowPriorityCue } from './opsQueuePreviewRowPriorityCue';
import { getOpsQueuePreviewRowReasonCue } from './opsQueuePreviewRowReasonCue';
import { getOpsQueuePreviewScopeLabel } from './opsQueuePreviewScope';

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

function getSummaryCardTone(kind: 'blocked' | 'needs_attention' | 'ready' | 'all') {
  switch (kind) {
    case 'blocked':
      return 'border-rose-200 bg-rose-50 text-rose-700';
    case 'needs_attention':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    case 'ready':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    default:
      return 'border-slate-200 bg-slate-50 text-slate-700';
  }
}

function getDayRunningCount(summary: DayRunningQueueSummary | null, filter: 'all' | DayRunningTriageFilter) {
  if (!summary) {
    return 0;
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

function getAttentionHeadline(summary: DayRunningQueueSummary | null) {
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

function getTopAttentionOrders(orders: OrderRecord[]) {
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

type OpsHomeReadinessState = {
  title: string;
  message: string;
  note: string;
  action: string;
  recoveryCommandLabel: string;
  recoveryCommand: string;
  guidanceTitle: string;
  guidanceSource: string;
  guidanceSteps: string[];
};

type OpsHomeRetryFeedback = {
  tone: 'warning' | 'success';
  checkedLabel: string;
  message: string;
  dismissLabel?: string;
};

function getReadinessState(error: unknown): OpsHomeReadinessState | null {
  if (!axios.isAxiosError(error)) {
    return null;
  }

  const detail = error.response?.data?.detail;
  if (!detail || detail.code !== 'local_dev_schema_stale') {
    return null;
  }

  return {
    title: detail.title || 'Local dev setup needs refresh',
    message:
      detail.message || 'Local dev data needs a schema refresh before Ops Home can load live queue data.',
    note: detail.note || 'This is a local BakeMate setup issue, not a bakery workflow status.',
    action: detail.action || 'Refresh or reseed the local dev database, then reload /ops.',
    recoveryCommandLabel: detail.recovery_command_label || 'Run locally from the BakeMate repo',
    recoveryCommand: detail.recovery_command || 'docker compose up --build -d',
    guidanceTitle: detail.guidance_title || 'How to recover locally',
    guidanceSource: detail.guidance_source || 'README.md and docs/developer_guide.md',
    guidanceSteps: detail.guidance_steps || [
      'Use the normal BakeMate local setup flow from README.md or docs/developer_guide.md to refresh the local dev environment.',
      'If your local BakeMate database was recreated, repopulate it using your usual local seed path before reloading /ops.',
      'Reload /ops after the local dev database is refreshed.',
    ],
  };
}

export default function OpsHome() {
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [summary, setSummary] = useState<DayRunningQueueSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [readinessState, setReadinessState] = useState<OpsHomeReadinessState | null>(null);
  const [retryFeedback, setRetryFeedback] = useState<OpsHomeRetryFeedback | null>(null);
  const [isRetryingReadiness, setIsRetryingReadiness] = useState(false);

  const loadOpsHome = useCallback(async (options?: { fromRetry?: boolean }) => {
    setIsLoading(true);
    setError(null);
    setReadinessState(null);
    if (options?.fromRetry) {
      setIsRetryingReadiness(true);
      setRetryFeedback(null);
    } else {
      setRetryFeedback(null);
    }
    try {
      const params = {
        day_running: undefined,
        action_class: undefined,
        urgency: undefined,
      };
      const [ordersData, summaryData] = await Promise.all([
        ordersApi.list(params),
        ordersApi.getDayRunningSummary(params),
      ]);
      setOrders(ordersData);
      setSummary(summaryData);
      if (options?.fromRetry) {
        setRetryFeedback(getGuardedOpsRetryFeedback('recovered'));
      } else {
        setRetryFeedback(null);
      }
    } catch (loadError) {
      const nextReadinessState = getReadinessState(loadError);
      if (nextReadinessState) {
        setReadinessState(nextReadinessState);
        setOrders([]);
        setSummary(null);
        if (options?.fromRetry) {
          setRetryFeedback(getGuardedOpsRetryFeedback('still_stale'));
        }
        return;
      }
      setRetryFeedback(null);
      setError('Unable to load Ops Home preview.');
    } finally {
      setIsLoading(false);
      setIsRetryingReadiness(false);
    }
  }, []);

  useEffect(() => {
    void loadOpsHome();
  }, [loadOpsHome]);

  const retryUiState = useMemo(
    () => getGuardedOpsRetryUiState(isRetryingReadiness),
    [isRetryingReadiness],
  );
  const topOrders = useMemo(() => getTopAttentionOrders(orders), [orders]);
  const blockedOrders = useMemo(
    () => topOrders.filter((order) => order.day_running_focus_summary.readiness_label === 'Blocked for today').slice(0, 3),
    [topOrders],
  );
  const attentionOrders = useMemo(
    () => topOrders.filter((order) => order.day_running_focus_summary.readiness_label === 'Needs attention today').slice(0, 3),
    [topOrders],
  );

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Preview</div>
            <h1 className="mt-2 text-3xl font-bold text-slate-900">Ops Home</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              A visible front door for BakeMate’s trusted day-running view. This preview reuses the same
              backend queue, readiness, and imported-payment trust signals already accepted in the order
              surfaces.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              className="inline-flex items-center rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              to="/orders"
            >
              Full queue
            </Link>
            <Link
              className="inline-flex items-center rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-700"
              to="/orders/imported"
            >
              Imported review
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        {[
          { key: 'all' as const, label: 'Visible day-running work' },
          { key: 'blocked' as const, label: 'Blocked for today' },
          { key: 'needs_attention' as const, label: 'Needs attention' },
          { key: 'ready' as const, label: 'Ready now' },
        ].map((card) => (
          <article
            key={card.key}
            className={`rounded-2xl border p-4 shadow-sm ${getSummaryCardTone(card.key)}`}
          >
            <div className="text-xs font-semibold uppercase tracking-wide">{card.label}</div>
            <div className="mt-3 text-3xl font-bold text-slate-900">
              {readinessState ? '—' : getDayRunningCount(summary, card.key)}
            </div>
          </article>
        ))}
      </section>

      {readinessState ? (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
          <div className="max-w-3xl">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">Local dev readiness</div>
            <h2 className="mt-2 text-2xl font-bold text-slate-900">{readinessState.title}</h2>
            <p className="mt-3 text-sm text-slate-700">{readinessState.message}</p>
            <p className="mt-2 text-sm text-slate-600">{readinessState.note}</p>
            <div className="mt-4 rounded-xl border border-amber-300 bg-white px-4 py-3 text-sm text-slate-700">
              <span className="font-semibold text-slate-900">Next step:</span> {readinessState.action}
            </div>
            <div className="mt-4 rounded-xl border border-slate-200 bg-white px-4 py-4 text-sm text-slate-700">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {readinessState.guidanceTitle}
              </div>
              <div className="mt-3 rounded-lg border border-slate-200 bg-slate-950 px-3 py-3">
                <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-300">
                  {readinessState.recoveryCommandLabel}
                </div>
                <code className="mt-2 block overflow-x-auto whitespace-pre-wrap break-all font-mono text-sm text-slate-100">
                  {readinessState.recoveryCommand}
                </code>
              </div>
              <ul className="mt-3 list-disc space-y-2 pl-5">
                {readinessState.guidanceSteps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ul>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  className="inline-flex items-center rounded-lg border border-amber-300 bg-amber-100 px-3 py-2 text-sm font-semibold text-amber-900 transition-colors hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-70"
                  onClick={() => {
                    if (isRetryingReadiness) {
                      return;
                    }
                    void loadOpsHome({ fromRetry: true });
                  }}
                  disabled={retryUiState.disabled}
                  type="button"
                >
                  {retryUiState.label}
                </button>
                <span className="text-xs text-slate-500">
                  {retryUiState.helperText}
                </span>
              </div>
              {retryFeedback && retryFeedback.tone === 'warning' ? (
                <div className="mt-3 rounded-xl border border-amber-200 bg-amber-100/70 px-4 py-3 text-sm text-amber-900">
                  <span className="font-semibold">{retryFeedback.checkedLabel}:</span> {retryFeedback.message}
                </div>
              ) : null}
              <div className="mt-3 text-xs text-slate-500">
                Canonical local setup guide: {readinessState.guidanceSource}
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {retryFeedback && !readinessState && retryFeedback.tone === 'success' ? (
        <section className="rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-emerald-900">
              <span className="font-semibold">{retryFeedback.checkedLabel}:</span> {retryFeedback.message}
            </div>
            <button
              className="inline-flex items-center rounded-lg border border-emerald-300 bg-white px-3 py-1.5 text-sm font-semibold text-emerald-900 transition-colors hover:bg-emerald-100"
              onClick={() => {
                setRetryFeedback((currentFeedback) => dismissGuardedOpsRetryFeedback(currentFeedback));
              }}
              type="button"
            >
              {retryFeedback.dismissLabel ?? 'Dismiss'}
            </button>
          </div>
        </section>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1.6fr),minmax(320px,0.9fr)]">
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">What needs attention now</h2>
              <p className="mt-1 text-sm text-slate-600">{getAttentionHeadline(summary)}</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <div className="rounded-xl bg-slate-100 px-4 py-3 text-right">
                <div className="text-xs uppercase tracking-wide text-slate-500">Queue preview</div>
                <div className="text-2xl font-semibold text-slate-900">{topOrders.length}</div>
                <div className="mt-1 text-xs font-semibold text-slate-600">{getOpsQueuePreviewPriorityLabel()}</div>
                <div className="mt-1 text-xs text-slate-500">{getOpsQueuePreviewScopeLabel(topOrders.length)}</div>
                <div className="mt-1 text-xs text-slate-500">{getOpsQueuePreviewDrillInAffordanceLabel()}</div>
              </div>
              <Link
                className="inline-flex items-center rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
                to="/orders"
              >
                View full queue
              </Link>
            </div>
          </div>

          {isLoading ? <p className="mt-4 text-sm text-slate-600">Loading ops preview...</p> : null}
          {error ? <p className="mt-4 text-sm text-rose-600">{error}</p> : null}
          {!isLoading && !error && topOrders.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">No visible ops work is currently available.</p>
          ) : null}

          <div className="mt-6 space-y-4">
            {topOrders.map((order) => {
              const queueBadge = getQueueBadge(order);
              const actionClassMeta = getActionClassMeta(order.ops_summary.action_class);
              const dayRunningMeta = getDayRunningMeta(order.day_running_focus_summary.readiness_label);
              const rowPriorityCue = getOpsQueuePreviewRowPriorityCue(order.queue_summary.urgency_label);
              const rowReasonCue = getOpsQueuePreviewRowReasonCue(
                order.day_running_focus_summary.readiness_label,
                order.day_running_focus_summary.queue_reason_preview,
              );
              const rowNextStepCue = getOpsQueuePreviewRowNextStepCue(
                order.day_running_focus_summary.readiness_label,
                order.day_running_focus_summary.queue_next_step_preview,
              );

              return (
                <article key={order.id} className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-900">
                        {order.order_number}
                        <span className="text-slate-400">•</span>
                        <span>{order.customer_summary.name || order.customer_summary.email || 'No customer'}</span>
                        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${queueBadge.className}`}>
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
                      <div className="text-sm font-semibold text-slate-900">{formatMoney(order.total_amount)}</div>
                      <div className="mt-1 text-xs uppercase tracking-wide text-slate-500">
                        {humanizeStatus(order.payment_status)}
                      </div>
                      <div className="mt-2 flex flex-col items-end gap-2">
                        <span
                          className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold ${rowPriorityCue.className}`}
                        >
                          {rowPriorityCue.label}
                        </span>
                        {rowReasonCue ? <div className="text-xs font-medium text-slate-600">{rowReasonCue}</div> : null}
                        {rowNextStepCue ? <div className="text-xs font-medium text-slate-600">{rowNextStepCue}</div> : null}
                      </div>
                    </div>
                  </div>

                  <div className={`mt-4 rounded-xl border p-4 ${dayRunningMeta}`}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-xs uppercase tracking-wide">Day-running readiness</div>
                        <div className="mt-1 text-sm font-semibold text-slate-900">
                          {order.day_running_focus_summary.readiness_label}
                        </div>
                        <div className="mt-1 text-sm text-slate-700">
                          {order.day_running_focus_summary.queue_reason_preview ??
                            order.day_running_focus_summary.reason_summary}
                        </div>
                        {order.day_running_focus_summary.queue_payment_trust_preview ? (
                          <div className="mt-2 text-xs font-medium text-sky-700">
                            {order.day_running_focus_summary.queue_payment_trust_preview}
                          </div>
                        ) : null}
                      </div>
                      <div className="text-right text-xs text-slate-600 max-w-[220px]">
                        {order.day_running_focus_summary.primary_blocker_label}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
                    <div>
                      <div className="text-xs uppercase tracking-wide text-amber-700">Next action</div>
                      <div className="mt-1 text-base font-semibold text-slate-900">{order.ops_summary.next_action}</div>
                      <div className="mt-1 text-sm text-slate-700">{order.ops_summary.ops_attention}</div>
                    </div>
                    <Link
                      className={`inline-flex rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${actionClassMeta.ctaClassName}`}
                      to={order.ops_summary.primary_cta_path}
                    >
                      {order.ops_summary.primary_cta_label}
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <aside className="space-y-6">
          <section className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Ops readout</h2>
            <div className="mt-4 space-y-3 text-sm text-slate-700">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Blocked first</div>
                <div className="mt-2 text-sm text-slate-900">
                  {blockedOrders.length > 0
                    ? blockedOrders.map((order) => order.order_number).join(', ')
                    : 'No blocked orders in the current queue preview.'}
                </div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Attention next</div>
                <div className="mt-2 text-sm text-slate-900">
                  {attentionOrders.length > 0
                    ? attentionOrders.map((order) => order.order_number).join(', ')
                    : 'No needs-attention orders in the current queue preview.'}
                </div>
              </div>
              <div className="rounded-xl border border-sky-200 bg-sky-50 p-4">
                <div className="text-xs font-semibold uppercase tracking-wide text-sky-700">Imported payment trust</div>
                <div className="mt-2 text-sm text-slate-900">
                  Imported orders keep the accepted payment trust boundary visible here as
                  <span className="font-semibold"> Payment trust: legacy-limited</span>.
                </div>
                <div className="mt-2 text-xs text-slate-600">
                  This preview stays informational only. It does not invent stronger historical payment certainty.
                </div>
              </div>
            </div>
          </section>
        </aside>
      </section>
    </div>
  );
}
