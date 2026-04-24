import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { OrdersSummaryPoint } from '../api/orders';

interface Props {
  data: OrdersSummaryPoint[];
  metric: 'orders' | 'revenue';
  onMetricToggle: () => void;
}

export default function OrdersChart({ data, metric, onMetricToggle }: Props) {
  return (
    <div className="bg-white rounded-2xl p-4 shadow">
      <div className="flex justify-between mb-2">
        <h3 className="font-medium">Orders</h3>
        <button
          className="text-sm text-blue-600"
          onClick={onMetricToggle}
          aria-label="Toggle metric"
        >
          {metric === 'orders' ? 'Show Revenue' : 'Show Orders'}
        </button>
      </div>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ left: 0, right: 0 }}>
            <defs>
              <linearGradient id="ordersColor" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f9a8d4" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#f9a8d4" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" hide />
            <YAxis hide />
            <Tooltip />
            <Area
              type="monotone"
              dataKey={metric}
              stroke="#f9a8d4"
              fillOpacity={1}
              fill="url(#ordersColor)"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

