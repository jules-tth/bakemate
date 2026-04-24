import { Link } from 'react-router-dom';

export default function Reports() {
  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Reports</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-white rounded shadow">
          <h2 className="text-lg font-semibold mb-2">Income Statement</h2>
          <p className="text-sm text-gray-600 mb-3">Revenue, COGS, expenses, and net profit.</p>
          <Link to="/reports/income-statement" className="inline-block px-3 py-2 bg-blue-600 text-white rounded-md text-sm">View</Link>
        </div>
        <div className="p-4 bg-white rounded shadow">
          <h2 className="text-lg font-semibold mb-2">Expenses Report</h2>
          <p className="text-sm text-gray-600 mb-3">Expenses by category and totals.</p>
          <Link to="/reports/expenses" className="inline-block px-3 py-2 bg-blue-600 text-white rounded-md text-sm">View</Link>
        </div>
        <div className="p-4 bg-white rounded shadow">
          <h2 className="text-lg font-semibold mb-2">Mileage Report</h2>
          <p className="text-sm text-gray-600 mb-3">Distance and reimbursement summary.</p>
          <Link to="/reports/mileage" className="inline-block px-3 py-2 bg-blue-600 text-white rounded-md text-sm">View</Link>
        </div>
      </div>
    </div>
  );
}
