import { expect, test } from 'vitest';

const assert = {
  equal: (actual: unknown, expected: unknown) => expect(actual).toBe(expected),
};

import { getOpsQueuePreviewDrillInAffordanceLabel } from './opsQueuePreviewDrillInAffordance.ts';

test('ops queue preview drill-in affordance makes order-detail opening explicit', () => {
  assert.equal(getOpsQueuePreviewDrillInAffordanceLabel(), 'Open any order for details.');
});
