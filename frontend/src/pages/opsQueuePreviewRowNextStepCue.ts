export function getOpsQueuePreviewRowNextStepCue(
  readinessLabel: string,
  queueNextStepPreview?: string | null,
): string | null {
  if (readinessLabel === 'Ready for today') {
    return null;
  }

  return queueNextStepPreview ?? null;
}
