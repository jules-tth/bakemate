interface Props {
  title: string;
  value: string | number;
  highlight?: boolean;
}

export default function DashboardCard({ title, value, highlight = false }: Props) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-sm text-gray-500">{title}</h2>
      <p className={`text-2xl font-bold mt-2 ${highlight ? 'text-red-600' : 'text-gray-900'}`}>{value}</p>
    </div>
  );
}

