import test from 'node:test';
import assert from 'node:assert/strict';

import { getOpsQueuePreviewRowPriorityCue } from './opsQueuePreviewRowPriorityCue.ts';

test('ops queue preview row priority cue reuses urgent queue meaning', () => {
  assert.deepEqual(getOpsQueuePreviewRowPriorityCue('Urgent'), {
    label: 'Priority: Urgent',
    className: 'border-rose-200 bg-rose-50 text-rose-700',
  });
});

test('ops queue preview row priority cue reuses today queue meaning', () => {
  assert.deepEqual(getOpsQueuePreviewRowPriorityCue('Today'), {
    label: 'Priority: Today',
    className: 'border-amber-200 bg-amber-50 text-amber-800',
  });
});

test('ops queue preview row priority cue reuses next-up queue meaning', () => {
  assert.deepEqual(getOpsQueuePreviewRowPriorityCue('Next up'), {
    label: 'Priority: Next up',
    className: 'border-sky-200 bg-sky-50 text-sky-800',
  });
});

test('ops queue preview row priority cue stays compact for watch-level work', () => {
  assert.deepEqual(getOpsQueuePreviewRowPriorityCue('Watch'), {
    label: 'Priority: Watch',
    className: 'border-slate-200 bg-slate-50 text-slate-700',
  });
});
