import test from 'node:test';
import assert from 'node:assert/strict';

import { getOpsQueuePreviewDrillInAffordanceLabel } from './opsQueuePreviewDrillInAffordance.ts';

test('ops queue preview drill-in affordance makes order-detail opening explicit', () => {
  assert.equal(getOpsQueuePreviewDrillInAffordanceLabel(), 'Open any order for details.');
});
