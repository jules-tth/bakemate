export function getOpsQueuePreviewPriorityLabel() {
  return 'Highest-priority orders first.';
}

export function getOpsQueuePreviewScopeLabel(previewItemCount: number) {
  if (previewItemCount === 1) {
    return 'Showing 1 preview item of the full queue.';
  }

  return `Showing ${previewItemCount} preview items of the full queue.`;
}

export function getOpsQueuePreviewDrillInAffordanceLabel() {
  return 'Open any order for details.';
}

export function getOpsQueuePreviewRowReasonCue(
  readinessLabel: string,
  queueReasonPreview?: string | null,
): string | null {
  if (readinessLabel === 'Ready for today') {
    return null;
  }

  return queueReasonPreview ?? null;
}

export function getOpsQueuePreviewRowNextStepCue(
  readinessLabel: string,
  queueNextStepPreview?: string | null,
): string | null {
  if (readinessLabel === 'Ready for today') {
    return null;
  }

  return queueNextStepPreview ?? null;
}

export function getOpsQueuePreviewRowPriorityCue(urgencyLabel: string) {
  switch (urgencyLabel) {
    case 'Urgent':
      return {
        label: 'Priority: Urgent',
        tone: 'urgent',
      };
    case 'Today':
      return {
        label: 'Priority: Today',
        tone: 'today',
      };
    case 'Next up':
      return {
        label: 'Priority: Next up',
        tone: 'next',
      };
    default:
      return {
        label: `Priority: ${urgencyLabel}`,
        tone: 'default',
      };
  }
}
