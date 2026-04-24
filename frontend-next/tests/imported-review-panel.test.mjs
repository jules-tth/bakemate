import test from 'node:test';
import assert from 'node:assert/strict';

import {
  describeImportReviewReason,
  getImportedReviewReasons,
  getImportedReviewSummary,
} from '../lib/imported-review-panel.ts';

test('describeImportReviewReason preserves accepted imported-review wording', () => {
  assert.equal(describeImportReviewReason('invoice_missing_fields'), 'Invoice data needs review');
  assert.equal(describeImportReviewReason('missing_contact_details'), 'Contact details missing');
});

test('getImportedReviewReasons maps all imported-review reasons into operator-safe labels', () => {
  assert.deepEqual(
    getImportedReviewReasons({
      review_reasons: ['overdue_payment_risk', 'unlinked_contact'],
    }),
    ['Overdue payment risk', 'Customer link needs review'],
  );
});

test('getImportedReviewSummary stays quiet for native BakeMate orders', () => {
  assert.equal(
    getImportedReviewSummary({ is_imported: false, needs_review: false, primary_review_reason: null }),
    'This order was created in BakeMate and does not need imported-data review.',
  );
});

test('getImportedReviewSummary uses the accepted primary imported-review reason when review is needed', () => {
  assert.equal(
    getImportedReviewSummary({
      is_imported: true,
      needs_review: true,
      primary_review_reason: 'overdue_payment_risk',
    }),
    'Overdue payment risk',
  );
});
