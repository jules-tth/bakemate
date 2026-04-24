interface Props {
  value: string;
  onChange: (value: string) => void;
}

const TABS = ['Open', 'Quoted', 'Completed', 'All'] as const;

export default function StatusTabs({ value, onChange }: Props) {
  return (
    <div role="tablist" className="flex gap-2 border-b mb-4">
      {TABS.map((tab) => (
        <button
          key={tab}
          role="tab"
          aria-selected={value === tab}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
            value === tab ? 'border-blue-600 text-blue-600' : 'border-transparent'
          }`}
          onClick={() => onChange(tab)}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}

