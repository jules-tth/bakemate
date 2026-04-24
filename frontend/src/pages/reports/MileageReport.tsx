import { useEffect, useMemo, useRef, useState } from 'react';
import { listMileageLogs } from '../../api/mileage';
import type { MileageLog } from '../../api/mileage';
import { exportElementPDF } from '../../utils/export';

export default function MileageReport() {
  const currentYear = new Date().getFullYear();
  const [mode, setMode] = useState<'year'|'range'>('year');
  const [year, setYear] = useState<string>(String(currentYear));
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [rows, setRows] = useState<MileageLog[]>([]);
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
      const data = await listMileageLogs({ start_date: startDate, end_date: endDate });
      if (!ignore) setRows(data);
    }
    load();
    return () => { ignore = true; };
  }, [startDate, endDate]);

  const totals = useMemo(() => {
    const totalMiles = rows.reduce((acc, r) => acc + (r.distance ?? 0), 0);
    const totalReimb = rows.reduce((acc, r) => acc + (r.reimbursement ?? 0), 0);
    return { totalMiles, totalReimb };
  }, [rows]);

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">Mileage Report</h1>
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
        <button className="ml-auto px-3 py-2 border rounded-md text-sm" onClick={()=>{ if(ref.current) exportElementPDF(ref.current, `Mileage — ${label}`, 'mileage-report.pdf'); }} disabled={!rows.length}>Export PDF</button>
      </div>
      <div ref={ref} className="bg-white rounded shadow p-4">
        {!rows.length ? (<p className="text-sm text-gray-600">Select a {mode==='year' ? 'year' : 'date range'} to preview.</p>) : (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">Mileage ({label})</h2>
            <div className="flex justify-between"><span>Total Distance</span><span className="tabular-nums">{totals.totalMiles.toFixed(1)} mi</span></div>
            <div className="flex justify-between"><span>Total Reimbursement</span><span className="tabular-nums">${totals.totalReimb.toFixed(2)}</span></div>
            <table className="w-full text-sm mt-2">
              <thead>
                <tr className="text-left">
                  <th className="py-1">Date</th>
                  <th className="py-1">Distance</th>
                  <th className="py-1">Reimbursed</th>
                  <th className="py-1">Description</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className="border-t">
                    <td className="py-1">{r.date}</td>
                    <td className="py-1 tabular-nums">{r.distance.toFixed(1)} mi</td>
                    <td className="py-1 tabular-nums">${r.reimbursement.toFixed(2)}</td>
                    <td className="py-1">{r.description ?? ''}</td>
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

