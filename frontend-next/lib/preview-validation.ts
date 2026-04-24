export const PREVIEW_VALIDATION_FEEDBACK_SUBJECT = 'BakeMate Next preview mismatch';

export const PREVIEW_VALIDATION_FEEDBACK_PROMPT =
  'Report the route tested, what differed from React/Vite, expected behavior, actual behavior, and any order number involved.';

export const PREVIEW_VALIDATION_TEST_PATH = [
  'Landing page',
  'Login',
  'Authenticated /ops',
  'Orders queue',
  'Order detail',
] as const;

export type PreviewValidationCheck = {
  label: string;
  detail: string;
  state: 'accepted' | 'bounded' | 'handoff';
};

export const PREVIEW_VALIDATION_CHECKS: PreviewValidationCheck[] = [
  {
    label: 'BM-093 path accepted',
    detail: 'Landing page -> login -> /ops -> /orders -> order detail remains the Next preview path to validate.',
    state: 'accepted',
  },
  {
    label: 'Read-only preview scope',
    detail: 'The Next surface validates navigation, queue readout, and order-detail entry only.',
    state: 'bounded',
  },
  {
    label: 'React/Vite remains trusted',
    detail: 'Use the current React/Vite app for live operations and deeper order work.',
    state: 'handoff',
  },
];

export function getPreviewValidationPathLabel() {
  return PREVIEW_VALIDATION_TEST_PATH.join(' -> ');
}

export function getPreviewValidationFeedbackHref() {
  const subject = encodeURIComponent(PREVIEW_VALIDATION_FEEDBACK_SUBJECT);
  const body = encodeURIComponent(PREVIEW_VALIDATION_FEEDBACK_PROMPT);

  return `mailto:?subject=${subject}&body=${body}`;
}

export function getPreviewValidationStateLabel(state: PreviewValidationCheck['state']) {
  if (state === 'accepted') {
    return 'Accepted';
  }

  if (state === 'handoff') {
    return 'Truth boundary';
  }

  return 'Preview only';
}
