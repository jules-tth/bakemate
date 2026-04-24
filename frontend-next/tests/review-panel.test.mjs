import test from 'node:test';
import assert from 'node:assert/strict';
import { getReviewCueRows, getReviewPrimaryBlocker } from '../lib/review-panel.ts';

const sampleOrder = {
  day_running_focus_summary: {
    readiness_label: 'Blocked for today',
    reason_summary: 'Attention: Deposit due',
    primary_blocker_label: 'Deposit due before production',
  },
  production_focus_summary: {
    readiness_label: 'Needs clarification',
    attention_note: 'Production basics still need review',
  },
  contact_focus_summary: {
    readiness_label: 'Ready to contact',
    attention_note: 'Best contact method is available',
  },
  review_focus_summary: {
    payment_trust_preview: 'Payment trust: legacy-limited',
  },
  payment_focus_summary: {
    trust_label: 'Legacy-limited',
    trust_note: 'Historical payment certainty is limited for imported data.',
  },
};

test('bm-086 review panel keeps the explicit primary blocker when present', () => {
  assert.equal(getReviewPrimaryBlocker(sampleOrder), 'Deposit due before production');
});

test('bm-086 review panel falls back to reason summary when no explicit blocker exists', () => {
  assert.equal(
    getReviewPrimaryBlocker({
      ...sampleOrder,
      day_running_focus_summary: {
        ...sampleOrder.day_running_focus_summary,
        primary_blocker_label: '',
      },
    }),
    'Attention: Deposit due',
  );
});

test('bm-086 review panel preserves accepted readiness and trust cues', () => {
  assert.deepEqual(getReviewCueRows(sampleOrder), [
    {
      label: 'Day-running readiness',
      value: 'Blocked for today',
      detail: 'Attention: Deposit due',
    },
    {
      label: 'Production',
      value: 'Needs clarification',
      detail: 'Production basics still need review',
    },
    {
      label: 'Contact',
      value: 'Ready to contact',
      detail: 'Best contact method is available',
    },
    {
      label: 'Payment trust',
      value: 'Payment trust: legacy-limited',
      detail: 'Historical payment certainty is limited for imported data.',
    },
  ]);
});
