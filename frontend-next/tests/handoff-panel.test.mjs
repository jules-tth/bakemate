import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getHandoffContactLines,
  getHandoffDestinationSummary,
  getHandoffMethodTone,
} from '../lib/handoff-panel.ts';

const order = {
  handoff_focus_summary: {
    contact_name: 'Jordan Lee',
    primary_contact: '(555) 010-4444',
    secondary_contact: 'jordan@example.com',
    destination_label: '123 Main St',
    destination_detail: 'Suite 4',
  },
};

test('getHandoffMethodTone highlights confirmed handoff method', () => {
  assert.equal(getHandoffMethodTone('Method confirmed'), 'badge badge-success');
});

test('getHandoffMethodTone highlights handoff methods needing confirmation', () => {
  assert.equal(getHandoffMethodTone('Method needs confirmation'), 'badge badge-warn');
});

test('getHandoffDestinationSummary keeps destination detail compact when it adds value', () => {
  assert.equal(getHandoffDestinationSummary(order), '123 Main St · Suite 4');
});

test('getHandoffContactLines returns only available operator contact clues', () => {
  assert.deepEqual(getHandoffContactLines(order), ['Jordan Lee', '(555) 010-4444', 'jordan@example.com']);
});
