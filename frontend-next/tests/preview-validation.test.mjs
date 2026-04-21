import test from 'node:test';
import assert from 'node:assert/strict';
import {
  PREVIEW_VALIDATION_CHECKS,
  PREVIEW_VALIDATION_FEEDBACK_PROMPT,
  getPreviewValidationFeedbackHref,
  getPreviewValidationPathLabel,
  getPreviewValidationStateLabel,
} from '../lib/preview-validation.ts';

test('bm-094 exposes the accepted bm-093 test path', () => {
  assert.equal(
    getPreviewValidationPathLabel(),
    'Landing page -> Login -> Authenticated /ops -> Orders queue -> Order detail',
  );
});

test('bm-094 keeps the React/Vite truth boundary explicit', () => {
  assert.ok(
    PREVIEW_VALIDATION_CHECKS.some((check) => (
      check.state === 'handoff' && check.detail.includes('React/Vite')
    )),
  );
});

test('bm-094 does not widen the checklist beyond the preview surface', () => {
  assert.deepEqual(
    PREVIEW_VALIDATION_CHECKS.map((check) => check.state),
    ['accepted', 'bounded', 'handoff'],
  );
});

test('bm-094 feedback affordance is concrete without a write workflow', () => {
  assert.ok(getPreviewValidationFeedbackHref().startsWith('mailto:?subject=BakeMate%20Next%20preview%20mismatch'));
  assert.match(PREVIEW_VALIDATION_FEEDBACK_PROMPT, /route tested/);
  assert.equal(getPreviewValidationStateLabel('bounded'), 'Preview only');
});
