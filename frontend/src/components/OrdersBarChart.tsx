import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export interface OrdersDatum {
  date: string;
  count: number;
}

export default function OrdersBarChart({ data }: { data: OrdersDatum[] }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-sm text-gray-500 mb-2">Orders</h2>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <XAxis dataKey="date" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" fill="#f9a8d4" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

