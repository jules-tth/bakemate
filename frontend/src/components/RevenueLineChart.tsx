import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export interface RevenueDatum {
  date: string;
  revenue: number;
}

export default function RevenueLineChart({ data }: { data: RevenueDatum[] }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-sm text-gray-500 mb-2">Revenue</h2>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="revenue" stroke="#60a5fa" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

