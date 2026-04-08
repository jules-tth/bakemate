export function getOpsQueuePreviewRowReasonCue(
  readinessLabel: string,
  queueReasonPreview?: string | null,
): string | null {
  if (readinessLabel === 'Ready for today') {
    return null;
  }

  return queueReasonPreview ?? null;
}
