import { expect, test } from 'vitest';

const assert = {
  equal: (actual: unknown, expected: unknown) => expect(actual).toBe(expected),
};

import { getOpsQueuePreviewRowNextStepCue } from './opsQueuePreviewRowNextStepCue.ts';

test('ops queue preview row next-step cue reuses trusted queue next-step meaning for blocked work', () => {
  assert.equal(
    getOpsQueuePreviewRowNextStepCue('Blocked for today', 'Next: finish invoice'),
    'Next: finish invoice',
  );
});

test('ops queue preview row next-step cue reuses trusted queue next-step meaning for attention work', () => {
  assert.equal(
    getOpsQueuePreviewRowNextStepCue('Needs attention today', 'Next: collect deposit'),
    'Next: collect deposit',
  );
});

test('ops queue preview row next-step cue stays quiet for ready work', () => {
  assert.equal(getOpsQueuePreviewRowNextStepCue('Ready for today', 'Next: review order'), null);
});

test('ops queue preview row next-step cue stays quiet when trusted queue guidance is absent', () => {
  assert.equal(getOpsQueuePreviewRowNextStepCue('Blocked for today', null), null);
});
