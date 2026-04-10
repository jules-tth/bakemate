import test from 'node:test';
import assert from 'node:assert/strict';
import { getCurrentFrontendHref } from '../lib/queue-ui.ts';

test('bm-085 current-app handoff helper returns null when current frontend base is unset', () => {
  const previous = process.env.NEXT_PUBLIC_CURRENT_FRONTEND_URL;
  delete process.env.NEXT_PUBLIC_CURRENT_FRONTEND_URL;
  assert.equal(getCurrentFrontendHref('/orders/abc123'), null);
  if (previous === undefined) {
    delete process.env.NEXT_PUBLIC_CURRENT_FRONTEND_URL;
  } else {
    process.env.NEXT_PUBLIC_CURRENT_FRONTEND_URL = previous;
  }
});

test('bm-085 current-app handoff helper builds a stable current-app order detail URL', () => {
  const previous = process.env.NEXT_PUBLIC_CURRENT_FRONTEND_URL;
  process.env.NEXT_PUBLIC_CURRENT_FRONTEND_URL = 'http://localhost:5174/';
  assert.equal(getCurrentFrontendHref('/orders/abc123'), 'http://localhost:5174/orders/abc123');
  if (previous === undefined) {
    delete process.env.NEXT_PUBLIC_CURRENT_FRONTEND_URL;
  } else {
    process.env.NEXT_PUBLIC_CURRENT_FRONTEND_URL = previous;
  }
});
