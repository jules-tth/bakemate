import { FormEvent, useEffect, useMemo, useState } from 'react';
import type { ColumnDef, SortingState, VisibilityState } from '@tanstack/react-table';
import { flexRender, getCoreRowModel, getPaginationRowModel, getSortedRowModel, useReactTable } from '@tanstack/react-table';
import { listMileageLogs, createMileageLog, updateMileageLog, deleteMileageLog } from '../api/mileage';
import type { MileageLog } from '../api/mileage';
import { Filter as FilterIcon, Download as DownloadIcon, Plus as PlusIcon } from 'lucide-react';
import { exportCSV } from '../utils/export';

export default function Mileage() {
  const [logs, setLogs] = useState<MileageLog[]>([]);
  const [form, setForm] = useState({ date: '', distance: '', description: '' });
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [viewItem, setViewItem] = useState<MileageLog | null>(null);
  const [minMiles, setMinMiles] = useState<string>('');
  const currentYear = new Date().getFullYear();
  const [yearFilter, setYearFilter] = useState(currentYear.toString());
  const [sorting, setSorting] = useState<SortingState>([{ id: 'date', desc: true }]);
  const [columnsOpen, setColumnsOpen] = useState(false);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data = await listMileageLogs();
        setLogs(data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchLogs();
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        const updated = await updateMileageLog(editingId, {
          date: form.date,
          distance: Number(form.distance),
          description: form.description,
        });
        setLogs((prev) => prev.map((l) => (l.id === updated.id ? updated : l)));
      } else {
        const newLog = await createMileageLog({
          date: form.date,
          distance: Number(form.distance),
          description: form.description,
        });
        setLogs((prev) => [...prev, newLog]);
      }
      setForm({ date: '', distance: '', description: '' });
      setEditingId(null);
      setShowModal(false);
    } catch (error) {
      console.error(error);
    }
  };

  function openEdit(log: MileageLog) {
    setEditingId(log.id);
    setForm({ date: log.date.slice(0,10), distance: String(log.distance), description: log.description ?? '' });
    setShowModal(true);
  }

  async function handleDelete(id: string) {
    const ok = window.confirm('Delete this log?');
    if (!ok) return;
    try {
      await deleteMileageLog(id);
      setLogs((prev) => prev.filter((l) => l.id !== id));
    } catch (err) {
      console.error(err);
      window.alert('Failed to delete log');
    }
  }

  const years = [currentYear, currentYear - 1, currentYear - 2, currentYear - 3, currentYear - 4];
  const filteredLogs = useMemo(() => {
    const byYear = yearFilter === 'all' ? logs : logs.filter((l) => (l.date || '').slice(0,4) === yearFilter);
    const byMiles = minMiles ? byYear.filter((l) => l.distance >= Number(minMiles)) : byYear;
    return [...byMiles].sort((a,b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [logs, yearFilter, minMiles]);

  const currency = useMemo(
    () => new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }),
    []
  );

  const columns = useMemo<ColumnDef<MileageLog>[]>(() => [
    { header: 'Date', accessorKey: 'date' },
    { header: 'Distance (mi)', accessorKey: 'distance', cell: ({ getValue }) => <span className="tabular-nums">{getValue<number>().toFixed(1)}</span> },
    { header: 'Reimbursed', accessorKey: 'reimbursement', cell: ({ getValue }) => <span className="tabular-nums">{currency.format(getValue<number>())}</span> },
    { header: 'Description', accessorKey: 'description' },
    { id: 'actions', header: 'Actions', cell: ({ row }) => (
      <details className="relative">
        <summary className="list-none cursor-pointer select-none px-2 py-1 border rounded-md text-xs inline-flex items-center gap-1">Actions<svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path d="M5.25 7.5L10 12.25L14.75 7.5H5.25Z"/></svg></summary>
        <div className="absolute z-10 mt-1 w-40 bg-white border rounded-md shadow">
          <button className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50" onClick={() => openEdit(row.original)}>Edit</button>
          <button className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50" onClick={() => setViewItem(row.original)}>View</button>
          <button className="w-full text-left px-3 py-2 text-sm text-rose-700 hover:bg-rose-50" onClick={() => handleDelete(row.original.id)}>Delete</button>
        </div>
      </details>
    )}
  ], [currency]);

  const table = useReactTable({
    data: filteredLogs,
    columns,
    state: { sorting, columnVisibility },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 25 } },
  });

  return (
    <>
    <div>
      <h1 className="mb-4 text-2xl font-bold">Mileage Logs</h1>

      <div className="mb-2 flex items-center gap-2 relative">
        <label className="sr-only" htmlFor="mileage-year">Year</label>
        <select id="mileage-year" className="border p-2 rounded-md text-sm" value={yearFilter} onChange={(e) => setYearFilter(e.target.value)}>
          {years.map((y) => (<option key={y} value={y.toString()}>{y}</option>))}
          <option value="all">All</option>
        </select>
        <button className="p-2 border rounded-md" onClick={() => setFiltersOpen((o)=>!o)} aria-label="Filter" aria-expanded={filtersOpen} aria-controls="mileage-filters">
          <FilterIcon size={16} />
        </button>
        {filtersOpen && (
          <div id="mileage-filters" className="absolute z-10 top-full mt-2 right-0 bg-white border rounded-md shadow p-3 w-56">
            <label className="block text-xs mb-1">Min miles</label>
            <input type="number" step="0.1" value={minMiles} onChange={(e)=>setMinMiles(e.target.value)} className="w-full border rounded p-2 text-sm" placeholder="0" />
            <div className="flex justify-between mt-2">
              <button className="text-xs underline" onClick={()=>setMinMiles('')}>Clear</button>
              <button className="text-xs underline" onClick={()=>setFiltersOpen(false)}>Close</button>
            </div>
          </div>
        )}
        <button className="p-2 border rounded-md" onClick={()=>exportCSV(filteredLogs,'mileage.csv')} aria-label="Download CSV"><DownloadIcon size={16} /></button>
        <button className="flex items-center gap-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm" onClick={()=>setShowModal(true)}>
          <PlusIcon size={16} /> Add Log
        </button>
        <div className="ml-auto relative">
          <button className="px-2 py-1 border rounded-md text-sm" onClick={()=>setColumnsOpen((o)=>!o)} aria-expanded={columnsOpen} aria-controls="mileage-columns-menu">Columns</button>
          {columnsOpen && (
            <div id="mileage-columns-menu" className="absolute right-0 mt-2 w-56 bg-white border rounded-md shadow p-2 z-10">
              <p className="px-1 pb-1 text-xs text-gray-500">Toggle columns</p>
              <div className="max-h-60 overflow-auto">
                {table.getAllLeafColumns().map((col) => (
                  <label key={col.id} className="flex items-center gap-2 px-1 py-1 text-sm">
                    <input type="checkbox" checked={col.getIsVisible()} onChange={col.getToggleVisibilityHandler()} />
                    <span>{String(col.columnDef.header)}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <table className="w-full text-sm bg-white rounded shadow border border-gray-200">
        <thead>
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((h) => (
                <th key={h.id} className="p-2 text-left cursor-pointer border-b" onClick={h.column.getToggleSortingHandler()}>
                  {flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="odd:bg-white even:bg-gray-50">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="p-2">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex justify-between items-center gap-4 p-2 text-sm">
        <button onClick={()=>table.previousPage()} disabled={!table.getCanPreviousPage()} className="px-2 py-1 border rounded-md disabled:opacity-50">Prev</button>
        <div className="flex items-center gap-2">
          <span>Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}</span>
          <label className="inline-flex items-center gap-1">
            <span>Rows:</span>
            <select
              value={String(table.getState().pagination.pageSize)}
              onChange={(e)=>{
                const v = e.target.value;
                if (v === 'all') table.setPageSize(table.getPrePaginationRowModel().rows.length);
                else table.setPageSize(Number(v));
              }}
              className="border rounded-md p-1"
              aria-label="Rows per page"
            >
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="all">All</option>
            </select>
          </label>
        </div>
        <button onClick={()=>table.nextPage()} disabled={!table.getCanNextPage()} className="px-2 py-1 border rounded-md disabled:opacity-50">Next</button>
      </div>

      {showModal && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50">
          <form onSubmit={handleCreate} className="space-y-2 rounded bg-white p-4 shadow w-80">
            <h2 className="text-lg font-semibold">{editingId ? 'Edit Log' : 'Add Log'}</h2>
            <input aria-label="date" className="w-full border p-2" type="date" value={form.date} onChange={(e)=>setForm({...form, date:e.target.value})} required />
            <input aria-label="distance" className="w-full border p-2" type="number" step="0.1" value={form.distance} onChange={(e)=>setForm({...form, distance:e.target.value})} placeholder="Miles" required />
            <input aria-label="description" className="w-full border p-2" value={form.description} onChange={(e)=>setForm({...form, description:e.target.value})} placeholder="Description" />
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="px-4 py-2" onClick={()=>{ setShowModal(false); setEditingId(null); }}>Cancel</button>
              <button type="submit" className="bg-blue-600 px-4 py-2 text-white">{editingId ? 'Save Changes' : 'Save'}</button>
            </div>
          </form>
        </div>
      )}
    </div>

      {viewItem && (
        <div className="fixed inset-0 bg-black/30 flex" role="dialog" aria-modal>
          <aside className="ml-auto h-full w-full max-w-md bg-white shadow-xl p-4 flex flex-col gap-2">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-lg font-semibold">Mileage Details</h2>
              <button className="px-2 py-1 border rounded-md" onClick={() => setViewItem(null)} aria-label="Close">Close</button>
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span className="text-gray-600">Date</span><span>{viewItem.date}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Distance</span><span className="tabular-nums">{viewItem.distance.toFixed(1)} mi</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Reimbursement</span><span className="tabular-nums">${viewItem.reimbursement.toFixed(2)}</span></div>
              <div className=""><span className="text-gray-600">Description</span><div>{viewItem.description ?? '-'}</div></div>
            </div>
          </aside>
        </div>
      )}
  </>
  );
}
