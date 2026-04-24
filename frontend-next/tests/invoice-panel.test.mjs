import test from 'node:test';
import assert from 'node:assert/strict';
import { getInvoiceReadinessTone, humanizeInvoiceStatus } from '../lib/invoice-panel.ts';

test('bm-088 invoice panel humanizes ready-to-send status', () => {
  assert.equal(humanizeInvoiceStatus('ready_to_send'), 'Ready to send');
});

test('bm-088 invoice panel keeps ready tone for invoice-safe states', () => {
  assert.equal(
    getInvoiceReadinessTone({ invoice_focus_summary: { status_label: 'ready_and_paid' } }),
    'ready',
  );
});

test('bm-088 invoice panel keeps blocked tone when invoice work is not ready', () => {
  assert.equal(
    getInvoiceReadinessTone({ invoice_focus_summary: { status_label: 'blocked' } }),
    'blocked',
  );
});
