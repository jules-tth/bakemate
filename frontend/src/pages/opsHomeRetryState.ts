export type GuardedOpsRetryUiState = {
  label: string;
  disabled: boolean;
  helperText: string;
};

export type GuardedOpsRetryFeedback = {
  tone: 'warning' | 'success';
  checkedLabel: string;
  message: string;
  dismissLabel?: string;
};

export function getGuardedOpsRetryUiState(isRetrying: boolean): GuardedOpsRetryUiState {
  if (isRetrying) {
    return {
      label: 'Checking /ops...',
      disabled: true,
      helperText: 'BakeMate is re-checking the normal local /ops view now.',
    };
  }

  return {
    label: 'Try /ops again',
    disabled: false,
    helperText: 'After you run the local recovery command above, re-check the normal /ops view here.',
  };
}

export function getGuardedOpsRetryFeedback(outcome: 'still_stale' | 'recovered'): GuardedOpsRetryFeedback {
  if (outcome === 'recovered') {
    return {
      tone: 'success',
      checkedLabel: 'Recovered just now',
      message: 'Local dev setup is ready again. Showing the normal /ops view now.',
      dismissLabel: 'Dismiss',
    };
  }

  return {
    tone: 'warning',
    checkedLabel: 'Checked just now',
    message: 'Local dev setup is still not ready. Verify the local recovery steps above, then try /ops again.',
  };
}

export function dismissGuardedOpsRetryFeedback(
  feedback: GuardedOpsRetryFeedback | null,
): GuardedOpsRetryFeedback | null {
  if (!feedback || feedback.tone !== 'success') {
    return feedback;
  }

  return null;
}
