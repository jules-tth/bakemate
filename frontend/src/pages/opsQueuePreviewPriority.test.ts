import test from 'node:test';
import assert from 'node:assert/strict';

import { getOpsQueuePreviewPriorityLabel } from './opsQueuePreviewPriority.ts';

test('ops queue preview priority label explains that healthy ops shows the top work first', () => {
  assert.equal(getOpsQueuePreviewPriorityLabel(), 'Highest-priority orders first.');
});
