import test from 'node:test';
import assert from 'node:assert/strict';

import { getOpsQueuePreviewScopeLabel } from './opsQueuePreviewScope.ts';

test('ops queue preview scope label makes singular preview scope explicit', () => {
  assert.equal(getOpsQueuePreviewScopeLabel(1), 'Showing 1 preview item of the full queue.');
});

test('ops queue preview scope label makes plural preview scope explicit', () => {
  assert.equal(getOpsQueuePreviewScopeLabel(5), 'Showing 5 preview items of the full queue.');
});

test('ops queue preview scope label stays explicit even when no preview rows are visible', () => {
  assert.equal(getOpsQueuePreviewScopeLabel(0), 'Showing 0 preview items of the full queue.');
});
