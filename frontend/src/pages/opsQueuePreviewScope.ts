export function getOpsQueuePreviewScopeLabel(previewItemCount: number) {
  if (previewItemCount === 1) {
    return 'Showing 1 preview item of the full queue.';
  }

  return `Showing ${previewItemCount} preview items of the full queue.`;
}
