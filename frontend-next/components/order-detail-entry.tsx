'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { fetchOrderDetail, type OrderDetailRecord } from '@/lib/orders';
import { getHandoffContactLines, getHandoffDestinationSummary, getHandoffMethodTone } from '@/lib/handoff-panel';
import { describeImportReviewReason, getImportedReviewReasons, getImportedReviewSummary } from '@/lib/imported-review-panel';
import { humanizeInvoiceStatus, getInvoiceReadinessTone } from '@/lib/invoice-panel';
import { describeAmountOwedNow, getPaymentTrustTone } from '@/lib/payment-panel';
import { getReviewCueRows, getReviewPrimaryBlocker } from '@/lib/review-panel';
import { formatBakeryDateTime, formatMoney, getCurrentFrontendHref, humanizeStatus } from '@/lib/queue-ui';

export function OrderDetailEntry({ orderId }: { orderId: string }) {
  const [order, setOrder] = useState<OrderDetailRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const nextOrder = await fetchOrderDetail(orderId);
        setOrder(nextOrder);
      } catch (nextError) {
        setError(nextError instanceof Error ? nextError.message : 'Unable to load order detail');
      } finally {
        setIsLoading(false);
      }
    }

    void load();
  }, [orderId]);

  if (isLoading) {
    return (
      <main className="shell">
        <section className="card muted">Loading authenticated order detail…</section>
      </main>
    );
  }

  if (error || !order) {
    return (
      <main className="shell">
        <section className="card error">{error || 'Order detail unavailable.'}</section>
      </main>
    );
  }

  const currentAppHref = getCurrentFrontendHref(order.ops_summary.primary_cta_path || `/orders/${order.id}`);
  const reviewCues = getReviewCueRows(order);
  const primaryBlocker = getReviewPrimaryBlocker(order);
  const paymentTrustTone = getPaymentTrustTone(order);
  const invoiceReadinessTone = getInvoiceReadinessTone(order);
  const handoffMethodTone = getHandoffMethodTone(order.handoff_focus_summary.method_status);
  const handoffContactLines = getHandoffContactLines(order);
  const handoffDestinationSummary = getHandoffDestinationSummary(order);
  const importedReviewSummary = getImportedReviewSummary(order);
  const importedReviewReasons = getImportedReviewReasons(order);

  return (
    <main className="shell">
      <div className="stack">
        <section className="card stack">
          <div className="row spread start">
            <div>
              <div className="label">Order detail entry</div>
              <h1 style={{ margin: '8px 0 0' }}>{order.order_number}</h1>
              <p className="muted" style={{ marginBottom: 0 }}>
                BM-086 upgrades the Next detail entry into a real review-first working surface while keeping deeper order
                work honestly handed off to the current app.
              </p>
            </div>
            <div className="row">
              <Link className="button" href="/orders">Back to queue</Link>
              {currentAppHref ? <a className="button primary" href={currentAppHref}>Continue in current app</a> : null}
            </div>
          </div>
        </section>

        <section className="grid cols-4">
          <article className="card">
            <div className="label">Customer</div>
            <div style={{ fontWeight: 700, marginTop: 6 }}>{order.review_focus_summary.customer_name}</div>
            <div className="muted" style={{ marginTop: 6 }}>{order.customer_summary.email || order.customer_summary.phone || 'No contact detail'}</div>
          </article>
          <article className="card">
            <div className="label">Due</div>
            <div style={{ fontWeight: 700, marginTop: 6 }}>{order.review_focus_summary.due_label || formatBakeryDateTime(order.due_date)}</div>
            <div className="muted" style={{ marginTop: 6 }}>{order.delivery_method || 'delivery TBD'}</div>
          </article>
          <article className="card">
            <div className="label">Status</div>
            <div style={{ fontWeight: 700, marginTop: 6 }}>{order.review_focus_summary.status_label || humanizeStatus(order.status)}</div>
            <div className="muted" style={{ marginTop: 6 }}>{humanizeStatus(order.payment_status)}</div>
          </article>
          <article className="card">
            <div className="label">Total</div>
            <div style={{ fontWeight: 700, marginTop: 6 }}>{formatMoney(order.total_amount)}</div>
            <div className="muted" style={{ marginTop: 6 }}>{order.review_focus_summary.item_count_label}</div>
          </article>
        </section>

        <section className="card stack">
          <div>
            <div className="label">Review-first surface</div>
            <div style={{ fontWeight: 700, marginTop: 6 }}>{order.review_focus_summary.item_summary}</div>
            <div className="muted" style={{ marginTop: 8 }}>{order.review_focus_summary.risk_note}</div>
          </div>

          <div className="grid cols-4">
            {reviewCues.map((cue) => (
              <article className="card" key={cue.label}>
                <div className="label">{cue.label}</div>
                <div style={{ fontWeight: 700, marginTop: 6 }}>{cue.value}</div>
                <div className="muted" style={{ marginTop: 6 }}>{cue.detail}</div>
              </article>
            ))}
          </div>

          {order.review_focus_summary.payment_trust_preview ? (
            <div className="trust-cue">{order.review_focus_summary.payment_trust_preview}</div>
          ) : null}

          {order.payment_focus_summary.historical_payment_label ? (
            <div className="card" style={{ padding: 14 }}>
              <div className="label">Imported payment trust</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.payment_focus_summary.historical_payment_label}</div>
              {order.payment_focus_summary.historical_payment_note ? (
                <div className="muted" style={{ marginTop: 6 }}>{order.payment_focus_summary.historical_payment_note}</div>
              ) : null}
            </div>
          ) : null}

          {order.review_focus_summary.missing_basics.length > 0 ? (
            <div className="card" style={{ padding: 14 }}>
              <div className="label">Missing basics</div>
              <ul style={{ margin: '10px 0 0', paddingLeft: 18 }}>
                {order.review_focus_summary.missing_basics.map((item) => (
                  <li key={item} className="muted">{item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="card" style={{ padding: 14 }}>
            <div className="label">Primary blocker</div>
            <div style={{ fontWeight: 700, marginTop: 6 }}>{primaryBlocker}</div>
            <div className="muted" style={{ marginTop: 6 }}>{order.day_running_focus_summary.reason_summary}</div>
          </div>

          <div className="card" style={{ padding: 14 }}>
            <div className="label">Next step</div>
            <div style={{ fontWeight: 700, marginTop: 6 }}>{order.review_focus_summary.next_step}</div>
            <div className="muted" style={{ marginTop: 6 }}>{order.review_focus_summary.next_step_detail}</div>
          </div>
        </section>

        <section className="card stack">
          <div className="label">Payment working surface</div>
          <div className="grid cols-4">
            <article className="card">
              <div className="label">Amount owed now</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{formatMoney(order.payment_focus_summary.amount_owed_now ?? 0)}</div>
              <div className="muted" style={{ marginTop: 6 }}>{describeAmountOwedNow(order.payment_focus_summary.collection_stage)}</div>
            </article>
            <article className="card">
              <div className="label">Payment state</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.payment_focus_summary.payment_state}</div>
              <div className="muted" style={{ marginTop: 6 }}>{order.payment_focus_summary.due_timing}</div>
            </article>
            <article className="card">
              <div className="label">Deposit status</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.payment_focus_summary.deposit_status}</div>
              <div className="muted" style={{ marginTop: 6 }}>Balance: {order.payment_focus_summary.balance_status}</div>
            </article>
            <article className="card">
              <div className="label">Trust</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.payment_focus_summary.trust_label}</div>
              <div className="muted" style={{ marginTop: 6 }}>{order.payment_focus_summary.trust_note}</div>
            </article>
          </div>

          <div className={`trust-cue${paymentTrustTone === 'legacy_limited' ? '' : ' trust-cue-neutral'}`}>
            {order.review_focus_summary.payment_trust_preview || `Payment trust: ${order.payment_focus_summary.trust_label}`}
          </div>

          {order.payment_focus_summary.historical_payment_label ? (
            <div className="card" style={{ padding: 14 }}>
              <div className="label">Historical payment</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.payment_focus_summary.historical_payment_label}</div>
              {order.payment_focus_summary.historical_payment_note ? (
                <div className="muted" style={{ marginTop: 6 }}>{order.payment_focus_summary.historical_payment_note}</div>
              ) : null}
            </div>
          ) : null}

          <div className="card" style={{ padding: 14 }}>
            <div className="label">Payment risk</div>
            <div style={{ fontWeight: 700, marginTop: 6 }}>{order.payment_focus_summary.risk_note}</div>
            <div className="muted" style={{ marginTop: 6 }}>{order.payment_focus_summary.next_step}</div>
            <div className="muted" style={{ marginTop: 6 }}>{order.payment_focus_summary.next_step_detail}</div>
          </div>
        </section>

        <section className="card stack">
          <div>
            <div className="label">Invoice working surface</div>
            <div style={{ fontWeight: 700, marginTop: 6 }}>{humanizeInvoiceStatus(order.invoice_focus_summary.status_label)}</div>
            <div className="muted" style={{ marginTop: 8 }}>{order.invoice_focus_summary.readiness_note}</div>
          </div>

          <div className="grid cols-4">
            <article className="card">
              <div className="label">Invoice readiness</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{humanizeInvoiceStatus(order.invoice_focus_summary.status_label)}</div>
              <div className="muted" style={{ marginTop: 6 }}>{invoiceReadinessTone === 'ready' ? 'Safe to assess for sending from the current order record.' : 'The current order record still blocks trustworthy invoice follow-up.'}</div>
            </article>
            <article className="card">
              <div className="label">Order identity</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.invoice_focus_summary.order_identity}</div>
              <div className="muted" style={{ marginTop: 6 }}>Invoice status: {humanizeStatus(order.invoice_summary.status)}</div>
            </article>
            <article className="card">
              <div className="label">Customer identity</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.invoice_focus_summary.customer_identity}</div>
              <div className="muted" style={{ marginTop: 6 }}>{order.customer_summary.email || order.customer_summary.phone || 'Customer contact detail is still limited.'}</div>
            </article>
            <article className="card">
              <div className="label">Amount context</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.invoice_focus_summary.amount_summary}</div>
              <div className="muted" style={{ marginTop: 6 }}>{order.invoice_focus_summary.payment_context}</div>
            </article>
          </div>

          <div className="grid cols-4">
            <div className="card" style={{ padding: 14 }}>
              <div className="label">Invoice blockers</div>
              {order.invoice_focus_summary.blockers.length > 0 ? (
                <ul style={{ margin: '10px 0 0', paddingLeft: 18 }}>
                  {order.invoice_focus_summary.blockers.map((item) => (
                    <li key={item} className="muted">{item}</li>
                  ))}
                </ul>
              ) : (
                <div className="muted" style={{ marginTop: 10 }}>No invoice blockers from the current order record.</div>
              )}
            </div>
            <div className="card" style={{ padding: 14 }}>
              <div className="label">Missing basics</div>
              {order.invoice_focus_summary.missing_basics.length > 0 ? (
                <ul style={{ margin: '10px 0 0', paddingLeft: 18 }}>
                  {order.invoice_focus_summary.missing_basics.map((item) => (
                    <li key={item} className="muted">{item}</li>
                  ))}
                </ul>
              ) : (
                <div className="muted" style={{ marginTop: 10 }}>No extra invoice basics are missing from the current order data.</div>
              )}
            </div>
            <div className="card" style={{ padding: 14, gridColumn: 'span 2' }}>
              <div className="label">Next invoice step</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.invoice_focus_summary.next_step}</div>
              <div className="muted" style={{ marginTop: 6 }}>{order.invoice_focus_summary.next_step_detail}</div>
            </div>
          </div>
        </section>

        <section className="card stack">
          <div>
            <div className="label">Handoff working surface</div>
            <div style={{ fontWeight: 700, marginTop: 6 }}>{order.handoff_focus_summary.readiness_note}</div>
            <div className="muted" style={{ marginTop: 8 }}>
              Timing, method, contact, and destination clues now stay inside the Next detail route for honest handoff scan parity.
            </div>
          </div>

          <div className="grid cols-4">
            <article className="card">
              <div className="label">Handoff time</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.handoff_focus_summary.handoff_time_label}</div>
              <div className="muted" style={{ marginTop: 6 }}>{order.review_focus_summary.due_label}</div>
            </article>
            <article className="card">
              <div className="label">Method status</div>
              <div style={{ marginTop: 8 }}>
                <span className={handoffMethodTone}>{order.handoff_focus_summary.method_status}</span>
              </div>
              <div className="muted" style={{ marginTop: 8 }}>{order.handoff_focus_summary.method_label}</div>
            </article>
            <article className="card">
              <div className="label">Primary contact</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.handoff_focus_summary.contact_name}</div>
              <div className="muted" style={{ marginTop: 6 }}>{order.handoff_focus_summary.primary_contact}</div>
              {order.handoff_focus_summary.secondary_contact ? (
                <div className="muted" style={{ marginTop: 6 }}>{order.handoff_focus_summary.secondary_contact}</div>
              ) : null}
            </article>
            <article className="card">
              <div className="label">Destination</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.handoff_focus_summary.destination_label}</div>
              <div className="muted" style={{ marginTop: 6 }}>{handoffDestinationSummary}</div>
            </article>
          </div>

          <div className="grid cols-4">
            <div className="card" style={{ padding: 14 }}>
              <div className="label">Contact clues</div>
              {handoffContactLines.length > 0 ? (
                <ul style={{ margin: '10px 0 0', paddingLeft: 18 }}>
                  {handoffContactLines.map((item) => (
                    <li key={item} className="muted">{item}</li>
                  ))}
                </ul>
              ) : (
                <div className="muted" style={{ marginTop: 10 }}>No operator-safe handoff contact clues are available yet.</div>
              )}
            </div>
            <div className="card" style={{ padding: 14 }}>
              <div className="label">Missing handoff basics</div>
              {order.handoff_focus_summary.missing_basics.length > 0 ? (
                <ul style={{ margin: '10px 0 0', paddingLeft: 18 }}>
                  {order.handoff_focus_summary.missing_basics.map((item) => (
                    <li key={item} className="muted">{item}</li>
                  ))}
                </ul>
              ) : (
                <div className="muted" style={{ marginTop: 10 }}>No extra handoff basics are missing from the current order data.</div>
              )}
            </div>
            <div className="card" style={{ padding: 14, gridColumn: 'span 2' }}>
              <div className="label">Next handoff step</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{order.handoff_focus_summary.next_step}</div>
              <div className="muted" style={{ marginTop: 6 }}>{order.handoff_focus_summary.next_step_detail}</div>
            </div>
          </div>
        </section>

        {order.is_imported ? (
          <section className="card stack">
            <div>
              <div className="label">Imported review</div>
              <div style={{ fontWeight: 700, marginTop: 6 }}>{importedReviewSummary}</div>
              <div className="muted" style={{ marginTop: 8 }}>
                Imported source, legacy status, and bounded review reasons now stay visible inside the Next detail route for operator-safe imported triage.
              </div>
            </div>

            <div className="grid cols-4">
              <article className="card">
                <div className="label">Imported from</div>
                <div style={{ fontWeight: 700, marginTop: 6 }}>{order.import_source || 'Imported workbook'}</div>
              </article>
              <article className="card">
                <div className="label">Legacy status</div>
                <div style={{ fontWeight: 700, marginTop: 6 }}>{order.legacy_status_raw || 'Not captured'}</div>
              </article>
              <article className="card">
                <div className="label">Primary review reason</div>
                <div style={{ fontWeight: 700, marginTop: 6 }}>{describeImportReviewReason(order.primary_review_reason)}</div>
              </article>
              <article className="card">
                <div className="label">Next review check</div>
                <div style={{ fontWeight: 700, marginTop: 6 }}>{order.review_next_check || 'No current follow-up check is suggested.'}</div>
              </article>
            </div>

            <div className="card" style={{ padding: 14 }}>
              <div className="label">Review reasons</div>
              {importedReviewReasons.length > 0 ? (
                <ul style={{ margin: '10px 0 0', paddingLeft: 18 }}>
                  {importedReviewReasons.map((item) => (
                    <li key={item} className="muted">{item}</li>
                  ))}
                </ul>
              ) : (
                <div className="muted" style={{ marginTop: 10 }}>No current imported-data review reasons are open for this order.</div>
              )}
            </div>
          </section>
        ) : null}

        <section className="card">
          <div className="label">Still handed off to the current app</div>
          <div className="muted" style={{ marginTop: 8 }}>
            Fuller order-detail parity, workflow editing, and any non-migrated operator flows remain intentionally outside BM-090. Use the current app CTA above for broader order-detail work not yet migrated.
          </div>
        </section>
      </div>
    </main>
  );
}
