import test from 'node:test';
import assert from 'node:assert/strict';

import {
  dismissGuardedOpsRetryFeedback,
  getGuardedOpsRetryFeedback,
  getGuardedOpsRetryUiState,
} from './opsHomeRetryState.ts';

test('guarded ops retry UI stays idle until a guarded retry is active', () => {
  assert.deepEqual(getGuardedOpsRetryUiState(false), {
    label: 'Try /ops again',
    disabled: false,
    helperText: 'After you run the local recovery command above, re-check the normal /ops view here.',
  });
});

test('guarded ops retry UI shows compact checking state while retry is in flight', () => {
  assert.deepEqual(getGuardedOpsRetryUiState(true), {
    label: 'Checking /ops...',
    disabled: true,
    helperText: 'BakeMate is re-checking the normal local /ops view now.',
  });
});

test('guarded ops retry feedback stays warning-scoped when local dev is still stale', () => {
  assert.deepEqual(getGuardedOpsRetryFeedback('still_stale'), {
    tone: 'warning',
    checkedLabel: 'Checked just now',
    message: 'Local dev setup is still not ready. Verify the local recovery steps above, then try /ops again.',
  });
});

test('guarded ops retry feedback shows compact success confirmation only on recovery', () => {
  assert.deepEqual(getGuardedOpsRetryFeedback('recovered'), {
    tone: 'success',
    checkedLabel: 'Recovered just now',
    message: 'Local dev setup is ready again. Showing the normal /ops view now.',
    dismissLabel: 'Dismiss',
  });
});

test('guarded ops retry success feedback can be dismissed back to the clean healthy state', () => {
  assert.equal(dismissGuardedOpsRetryFeedback(getGuardedOpsRetryFeedback('recovered')), null);
});

test('guarded ops retry warning feedback does not get cleared by success dismiss handling', () => {
  const warningFeedback = getGuardedOpsRetryFeedback('still_stale');
  assert.deepEqual(dismissGuardedOpsRetryFeedback(warningFeedback), warningFeedback);
});
