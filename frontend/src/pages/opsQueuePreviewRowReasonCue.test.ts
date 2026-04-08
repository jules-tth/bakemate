import test from 'node:test';
import assert from 'node:assert/strict';

import { getOpsQueuePreviewRowReasonCue } from './opsQueuePreviewRowReasonCue.ts';

test('ops queue preview row reason cue reuses trusted queue reason meaning for blocked work', () => {
  assert.equal(
    getOpsQueuePreviewRowReasonCue('Blocked for today', 'Attention: Invoice basics missing'),
    'Attention: Invoice basics missing',
  );
});

test('ops queue preview row reason cue reuses trusted queue reason meaning for attention work', () => {
  assert.equal(
    getOpsQueuePreviewRowReasonCue('Needs attention today', 'Attention: Deposit due'),
    'Attention: Deposit due',
  );
});

test('ops queue preview row reason cue stays quiet for ready work', () => {
  assert.equal(getOpsQueuePreviewRowReasonCue('Ready for today', 'Attention: Review order'), null);
});

test('ops queue preview row reason cue stays quiet when trusted queue guidance is absent', () => {
  assert.equal(getOpsQueuePreviewRowReasonCue('Blocked for today', null), null);
});
