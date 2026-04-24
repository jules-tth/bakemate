import { expect, test } from 'vitest';

const assert = {
  equal: (actual: unknown, expected: unknown) => expect(actual).toBe(expected),
};

import { getOpsQueuePreviewPriorityLabel } from './opsQueuePreviewPriority.ts';

test('ops queue preview priority label explains that healthy ops shows the top work first', () => {
  assert.equal(getOpsQueuePreviewPriorityLabel(), 'Highest-priority orders first.');
});
