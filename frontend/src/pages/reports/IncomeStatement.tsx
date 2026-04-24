import { useEffect, useMemo, useRef, useState } from 'react';
import { getProfitAndLoss } from '../../api/reports';
import type { ProfitAndLoss } from '../../api/reports';
import { exportElementPDF } from '../../utils/export';

function yyyy(n: number) { return String(n); }

export default function IncomeStatement() {
  const now = new Date();
  const currentYear = now.getFullYear();
  const [mode, setMode] = useState<'year' | 'range'>('year');
  const [year, setYear] = useState<string>(yyyy(currentYear));
  const [start, setStart] = useState<string>('');
  const [end, setEnd] = useState<string>('');
  const [data, setData] = useState<ProfitAndLoss | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  const { startDate, endDate, label } = useMemo(() => {
    if (mode === 'year') {
      const y = parseInt(year, 10);
      const s = new Date(y, 0, 1);
      const e = new Date(y, 11, 31);
      return { startDate: s.toISOString().slice(0,10), endDate: e.toISOString().slice(0,10), label: year };
    }
    return { startDate: start, endDate: end, label: `${start} → ${end}` };
  }, [mode, year, start, end]);

  useEffect(() => {
    let ignore = false;
    async function load() {
      if (!startDate || !endDate) return;
      const r = await getProfitAndLoss(startDate, endDate);
      if (!ignore) setData(r);
    }
    load();
    return () => { ignore = true; };
  }, [startDate, endDate]);

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">Income Statement</h1>
      <div className="flex items-center gap-2">
        <label className="inline-flex items-center gap-1 text-sm">
          <input type="radio" checked={mode==='year'} onChange={()=>setMode('year')} /> Year
        </label>
        <label className="inline-flex items-center gap-1 text-sm">
          <input type="radio" checked={mode==='range'} onChange={()=>setMode('range')} /> Date range
        </label>
        {mode==='year' ? (
          <select className="border rounded-md p-2 text-sm" value={year} onChange={(e)=>setYear(e.target.value)}>
            {[0,1,2,3,4].map(n=>{
              const y = String(currentYear-n);
              return <option key={y} value={y}>{y}</option>
            })}
          </select>
        ) : (
          <div className="flex items-center gap-2">
            <input type="date" className="border p-2 rounded-md text-sm" value={start} onChange={e=>setStart(e.target.value)} />
            <span>to</span>
            <input type="date" className="border p-2 rounded-md text-sm" value={end} onChange={e=>setEnd(e.target.value)} />
          </div>
        )}
        <button
          className="ml-auto px-3 py-2 border rounded-md text-sm"
          onClick={() => { if(ref.current) exportElementPDF(ref.current, `Income Statement — ${label}`, 'income-statement.pdf'); }}
          disabled={!data}
        >
          Export PDF
        </button>
      </div>
      <div ref={ref} className="bg-white rounded shadow p-4">
        {!data ? (
          <p className="text-sm text-gray-600">Select a {mode==='year' ? 'year' : 'date range'} to preview.</p>) : (
          <div>
            <h2 className="text-lg font-semibold mb-2">Income Statement ({label})</h2>
            <div className="space-y-1">
              <div className="flex justify-between"><span>Total Revenue</span><span className="tabular-nums">${data.total_revenue.toFixed(2)}</span></div>
              <div className="flex justify-between"><span>Cost of Goods Sold</span><span className="tabular-nums">${data.cost_of_goods_sold.toFixed(2)}</span></div>
              <div className="flex justify-between font-medium"><span>Gross Profit</span><span className="tabular-nums">${data.gross_profit.toFixed(2)}</span></div>
              <div className="mt-2">
                <div className="flex justify-between"><span>Operating Expenses</span><span className="tabular-nums">${data.operating_expenses.total.toFixed(2)}</span></div>
                <ul className="mt-1 text-sm text-gray-600">
                  {Object.entries(data.operating_expenses.by_category).map(([k,v]) => (
                    <li key={k} className="flex justify-between"><span>{k}</span><span className="tabular-nums">${v.toFixed(2)}</span></li>
                  ))}
                </ul>
              </div>
              <div className="flex justify-between font-semibold mt-2"><span>Net Profit</span><span className="tabular-nums">${data.net_profit.toFixed(2)}</span></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

