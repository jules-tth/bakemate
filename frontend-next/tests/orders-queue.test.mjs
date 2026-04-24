import test from 'node:test';
import assert from 'node:assert/strict';
import { getSortedOrdersQueue } from '../lib/queue-ui.ts';

test('next orders queue preserves accepted urgency-first ordering', () => {
  const orders = [
    {
      id: 'later-urgent',
      due_date: '2026-04-10T15:00:00Z',
      queue_summary: { urgency_rank: 1 },
    },
    {
      id: 'earlier-urgent',
      due_date: '2026-04-09T15:00:00Z',
      queue_summary: { urgency_rank: 1 },
    },
    {
      id: 'next-rank',
      due_date: '2026-04-08T15:00:00Z',
      queue_summary: { urgency_rank: 2 },
    },
  ];

  const sorted = getSortedOrdersQueue(orders);
  assert.deepEqual(
    sorted.map((order) => order.id),
    ['earlier-urgent', 'later-urgent', 'next-rank'],
  );
});
