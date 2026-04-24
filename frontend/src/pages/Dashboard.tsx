import { useEffect, useState } from 'react';
import DashboardCard from '../components/DashboardCard';
import OrdersBarChart from '../components/OrdersBarChart';
import RevenueLineChart from '../components/RevenueLineChart';
import {
  getDashboardSummary,
  getOrdersOverTime,
  getRevenueOverTime,
  type DashboardSummary,
  type OrdersOverTime,
  type RevenueOverTime,
} from '../api/dashboard';

const Dashboard: React.FC = () => {
  const [range, setRange] = useState('YTD');
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [orders, setOrders] = useState<OrdersOverTime[]>([]);
  const [revenue, setRevenue] = useState<RevenueOverTime[]>([]);

  useEffect(() => {
    async function load() {
      const [s, o, r] = await Promise.all([
        getDashboardSummary(range),
        getOrdersOverTime(range),
        getRevenueOverTime(range),
      ]);
      setSummary(s);
      setOrders(o);
      setRevenue(r);
    }
    load();
  }, [range]);

  const revenueDisplay = summary ? `$${summary.revenue.toLocaleString()}` : '-';
  const ordersDisplay = summary ? summary.total_orders.toString() : '-';
  const lowDisplay = summary ? summary.ingredients_low.toString() : '-';
  const lowHighlight = !!summary && summary.ingredients_low > 0;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <label className="text-sm">
          <span className="mr-2">Date Range</span>
          <select
            aria-label="Date Range"
            value={range}
            onChange={(e) => setRange(e.target.value)}
            className="border rounded p-1"
          >
            <option value="YTD">Year-to-Date</option>
            <option value="2024">2024</option>
            <option value="2025">2025</option>
          </select>
        </label>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <DashboardCard title="Revenue" value={revenueDisplay} />
        <DashboardCard title="Total Orders" value={ordersDisplay} />
        <DashboardCard title="Ingredients Low" value={lowDisplay} highlight={lowHighlight} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        <OrdersBarChart data={orders} />
        <RevenueLineChart data={revenue} />
      </div>
    </div>
  );
};

export default Dashboard;
