type OpsQueuePreviewRowPriorityCue = {
  label: string;
  className: string;
};

export function getOpsQueuePreviewRowPriorityCue(urgencyLabel: string): OpsQueuePreviewRowPriorityCue {
  switch (urgencyLabel) {
    case 'Urgent':
      return {
        label: 'Priority: Urgent',
        className: 'border-rose-200 bg-rose-50 text-rose-700',
      };
    case 'Today':
      return {
        label: 'Priority: Today',
        className: 'border-amber-200 bg-amber-50 text-amber-800',
      };
    case 'Next up':
      return {
        label: 'Priority: Next up',
        className: 'border-sky-200 bg-sky-50 text-sky-800',
      };
    default:
      return {
        label: `Priority: ${urgencyLabel}`,
        className: 'border-slate-200 bg-slate-50 text-slate-700',
      };
  }
}
