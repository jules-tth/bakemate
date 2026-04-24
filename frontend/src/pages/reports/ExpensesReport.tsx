import { useEffect, useMemo, useRef, useState } from 'react';
import { listExpenses } from '../../api/expenses';
import type { Expense } from '../../api/expenses';
import { exportElementPDF } from '../../utils/export';

export default function ExpensesReport() {
  const currentYear = new Date().getFullYear();
  const [mode, setMode] = useState<'year'|'range'>('year');
  const [year, setYear] = useState<string>(String(currentYear));
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [rows, setRows] = useState<Expense[]>([]);
  const ref = useRef<HTMLDivElement>(null);

  const { startDate, endDate, label } = useMemo(() => {
    if (mode==='year') {
      const y = parseInt(year, 10);
      const s = new Date(y,0,1).toISOString().slice(0,10);
      const e = new Date(y,11,31).toISOString().slice(0,10);
      return { startDate: s, endDate: e, label: year };
    }
    return { startDate: start, endDate: end, label: `${start} → ${end}` };
  }, [mode, year, start, end]);

  useEffect(() => {
    let ignore = false;
    async function load() {
      if (!startDate || !endDate) return;
      const data = await listExpenses({ start_date: startDate, end_date: endDate });
      if (!ignore) setRows(data);
    }
    load();
    return () => { ignore = true; };
  }, [startDate, endDate]);

  const byCategory = useMemo(() => {
    const map = new Map<string, number>();
    for (const r of rows) {
      const key = r.category ?? 'other';
      map.set(key, (map.get(key) ?? 0) + (r.amount ?? 0));
    }
    return Array.from(map.entries()).sort((a,b)=>b[1]-a[1]);
  }, [rows]);

  const total = useMemo(() => rows.reduce((acc, r) => acc + (r.amount ?? 0), 0), [rows]);

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">Expenses Report</h1>
      <div className="flex items-center gap-2">
        <label className="inline-flex items-center gap-1 text-sm"><input type="radio" checked={mode==='year'} onChange={()=>setMode('year')} /> Year</label>
        <label className="inline-flex items-center gap-1 text-sm"><input type="radio" checked={mode==='range'} onChange={()=>setMode('range')} /> Date range</label>
        {mode==='year' ? (
          <select className="border rounded-md p-2 text-sm" value={year} onChange={(e)=>setYear(e.target.value)}>
            {[0,1,2,3,4].map(n=>{ const y=String(currentYear-n); return <option key={y} value={y}>{y}</option>; })}
          </select>
        ) : (
          <div className="flex items-center gap-2">
            <input type="date" className="border p-2 rounded-md text-sm" value={start} onChange={e=>setStart(e.target.value)} />
            <span>to</span>
            <input type="date" className="border p-2 rounded-md text-sm" value={end} onChange={e=>setEnd(e.target.value)} />
          </div>
        )}
        <button className="ml-auto px-3 py-2 border rounded-md text-sm" onClick={()=>{ if(ref.current) exportElementPDF(ref.current, `Expenses — ${label}`, 'expenses-report.pdf'); }} disabled={!rows.length}>Export PDF</button>
      </div>
      <div ref={ref} className="bg-white rounded shadow p-4">
        {!rows.length ? (<p className="text-sm text-gray-600">Select a {mode==='year' ? 'year' : 'date range'} to preview.</p>) : (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">Expenses ({label})</h2>
            <div className="flex justify-between font-medium"><span>Total</span><span className="tabular-nums">${total.toFixed(2)}</span></div>
            <h3 className="font-semibold mt-2">By Category</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left">
                  <th className="py-1">Category</th>
                  <th className="py-1">Amount</th>
                </tr>
              </thead>
              <tbody>
                {byCategory.map(([k,v]) => (
                  <tr key={k} className="border-t">
                    <td className="py-1">{k}</td>
                    <td className="py-1 tabular-nums">${v.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

