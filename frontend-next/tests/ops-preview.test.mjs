import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getOpsQueuePreviewDrillInAffordanceLabel,
  getOpsQueuePreviewPriorityLabel,
  getOpsQueuePreviewRowNextStepCue,
  getOpsQueuePreviewRowPriorityCue,
  getOpsQueuePreviewRowReasonCue,
  getOpsQueuePreviewScopeLabel,
} from '../lib/ops-preview.ts';

test('next ops preview keeps the accepted priority label', () => {
  assert.equal(getOpsQueuePreviewPriorityLabel(), 'Highest-priority orders first.');
});

test('next ops preview keeps the accepted drill-in affordance label', () => {
  assert.equal(getOpsQueuePreviewDrillInAffordanceLabel(), 'Open any order for details.');
});

test('next ops preview keeps explicit preview scope labeling', () => {
  assert.equal(getOpsQueuePreviewScopeLabel(3), 'Showing 3 preview items of the full queue.');
});

test('next ops preview reason cue stays exception-only', () => {
  assert.equal(getOpsQueuePreviewRowReasonCue('Blocked for today', 'Attention: Deposit due'), 'Attention: Deposit due');
  assert.equal(getOpsQueuePreviewRowReasonCue('Ready for today', 'Attention: Review order'), null);
});

test('next ops preview next-step cue stays exception-only', () => {
  assert.equal(getOpsQueuePreviewRowNextStepCue('Needs attention today', 'Next: collect deposit'), 'Next: collect deposit');
  assert.equal(getOpsQueuePreviewRowNextStepCue('Ready for today', 'Next: review order'), null);
});

test('next ops preview priority cue keeps urgent wording', () => {
  assert.deepEqual(getOpsQueuePreviewRowPriorityCue('Urgent'), { label: 'Priority: Urgent', tone: 'urgent' });
});
