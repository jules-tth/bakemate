interface Props {
  value: string;
  onChange: (value: string) => void;
}

export default function DateRangePicker({ value, onChange }: Props) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border rounded-md p-2 text-sm"
      aria-label="Date range"
    >
      <option value="current-month">Current Month</option>
      <option value="ytd">Year-to-Date</option>
      <option value="2-years">Last 2 Years</option>
      <option value="all">All</option>
    </select>
  );
}

