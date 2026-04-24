import { FormEvent, useEffect, useMemo, useState } from 'react';
import type { ColumnDef, SortingState, VisibilityState } from '@tanstack/react-table';
import { flexRender, getCoreRowModel, getPaginationRowModel, getSortedRowModel, useReactTable } from '@tanstack/react-table';
import { listExpenses, createExpense, updateExpense, deleteExpense } from '../api/expenses';
import type { Expense } from '../api/expenses';
import { Filter as FilterIcon, Download as DownloadIcon, Plus as PlusIcon } from 'lucide-react';
import { exportCSV } from '../utils/export';

export default function Expenses() {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [form, setForm] = useState({
    description: '',
    amount: '',
    date: '',
    category: ''
  });
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [viewItem, setViewItem] = useState<Expense | null>(null);
  const currentYear = new Date().getFullYear();
  const [yearFilter, setYearFilter] = useState(currentYear.toString());
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [sorting, setSorting] = useState<SortingState>([{ id: 'date', desc: true }]);
  const [columnsOpen, setColumnsOpen] = useState(false);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});

  useEffect(() => {
    const fetchExpenses = async () => {
      try {
        const data = await listExpenses();
        setExpenses(data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchExpenses();
  }, []);

  const years = [currentYear, currentYear - 1, currentYear - 2, currentYear - 3, currentYear - 4];

  const filteredExpenses = useMemo(() => {
    const filtered =
      yearFilter === 'all'
        ? expenses
        : expenses.filter((e) => (e.date || '').slice(0, 4) === yearFilter);
    const catFiltered = selectedCategories.length
      ? filtered.filter((e) => (e.category ? selectedCategories.includes(e.category) : false))
      : filtered;
    return [...catFiltered].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    );
  }, [expenses, yearFilter, selectedCategories]);

  const currency = useMemo(
    () => new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }),
    []
  );
  const columns = useMemo<ColumnDef<Expense>[]>(
    () => [
      { accessorKey: 'date', header: 'Date' },
      { accessorKey: 'description', header: 'Description' },
      { accessorKey: 'category', header: 'Category' },
      {
        accessorKey: 'amount',
        header: 'Amount',
        cell: ({ getValue }) => (
          <span className="tabular-nums">{currency.format(getValue<number>())}</span>
        ),
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <details className="relative">
            <summary className="list-none cursor-pointer select-none px-2 py-1 border rounded-md text-xs inline-flex items-center gap-1">
              Actions
              <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path d="M5.25 7.5L10 12.25L14.75 7.5H5.25Z"/></svg>
            </summary>
            <div className="absolute z-10 mt-1 w-40 bg-white border rounded-md shadow">
              <button className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50" onClick={() => openEdit(row.original)}>Edit</button>
              <button className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50" onClick={() => setViewItem(row.original)}>View</button>
              <button className="w-full text-left px-3 py-2 text-sm text-rose-700 hover:bg-rose-50" onClick={() => handleDelete(row.original.id)}>Delete</button>
            </div>
          </details>
        ),
      }
    ],
    [currency]
  );

  const table = useReactTable({
    data: filteredExpenses,
    columns,
    state: { sorting, columnVisibility },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 25 } },
  });

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        const updated = await updateExpense(editingId, {
          description: form.description,
          amount: Number(form.amount),
          date: form.date,
          category: form.category || undefined,
        });
        setExpenses((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
      } else {
        const newExpense = await createExpense({
          description: form.description,
          amount: Number(form.amount),
          date: form.date,
          category: form.category || undefined,
        });
        setExpenses((prev) => [...prev, newExpense]);
      }
      setForm({ description: '', amount: '', date: '', category: '' });
      setEditingId(null);
      setShowModal(false);
    } catch (error) {
      console.error(error);
    }
  };

  function openEdit(exp: Expense) {
    setEditingId(exp.id);
    setForm({
      description: exp.description,
      amount: String(exp.amount ?? ''),
      date: (exp.date || '').slice(0, 10),
      category: exp.category ?? '',
    });
    setShowModal(true);
  }

  async function handleDelete(id: string) {
    const ok = window.confirm('Delete this expense?');
    if (!ok) return;
    try {
      await deleteExpense(id);
      setExpenses((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      console.error(err);
      window.alert('Failed to delete expense');
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Expenses</h1>

      <div className="mb-2 flex items-center gap-2 relative">
        <label className="sr-only" htmlFor="expenses-year">Year</label>
        <select
          id="expenses-year"
          aria-label="year"
          className="border p-2 rounded-md text-sm"
          value={yearFilter}
          onChange={(e) => setYearFilter(e.target.value)}
        >
          {years.map((y) => (
            <option key={y} value={y.toString()}>
              {y}
            </option>
          ))}
          <option value="all">All Years</option>
        </select>
        <button
          className="p-2 border rounded-md"
          onClick={() => setFiltersOpen((o) => !o)}
          aria-label="Filter"
          aria-expanded={filtersOpen}
          aria-controls="expenses-filters"
        >
          <FilterIcon size={16} />
        </button>
        {filtersOpen && (
          <div id="expenses-filters" className="absolute z-10 top-full mt-2 right-0 bg-white border rounded-md shadow p-3 w-56">
            <p className="text-xs mb-1">Categories</p>
            <div className="max-h-56 overflow-auto">
              {['ingredients','supplies','utilities','rent','marketing','fees','other'].map((c) => (
                <label key={c} className="flex items-center gap-2 py-1 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedCategories.includes(c)}
                    onChange={(e) => {
                      setSelectedCategories((prev) => e.target.checked ? [...prev, c] : prev.filter(v => v!==c));
                    }}
                  />
                  <span>{c}</span>
                </label>
              ))}
            </div>
            <div className="flex justify-between mt-2">
              <button className="text-xs underline" onClick={() => setSelectedCategories([])}>Clear</button>
              <button className="text-xs underline" onClick={() => setFiltersOpen(false)}>Close</button>
            </div>
          </div>
        )}
        <button
          className="p-2 border rounded-md"
          onClick={() => exportCSV(filteredExpenses, 'expenses.csv')}
          aria-label="Download CSV"
        >
          <DownloadIcon size={16} />
        </button>
        <button
          className="flex items-center gap-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm"
          onClick={() => setShowModal(true)}
        >
          <PlusIcon size={16} /> Add Expense
        </button>
        <div className="ml-auto relative">
          <button
            className="px-2 py-1 border rounded-md text-sm"
            onClick={() => setColumnsOpen((o) => !o)}
            aria-expanded={columnsOpen}
            aria-controls="expenses-columns-menu"
          >
            Columns
          </button>
          {columnsOpen && (
            <div id="expenses-columns-menu" className="absolute right-0 mt-2 w-56 bg-white border rounded-md shadow p-2 z-10">
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
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="p-2 text-left cursor-pointer border-b" onClick={header.column.getToggleSortingHandler()}>
                  {flexRender(
                    header.column.columnDef.header,
                    header.getContext()
                  )}
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
        <button onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()} className="px-2 py-1 border rounded-md disabled:opacity-50">Prev</button>
        <div className="flex items-center gap-2">
          <span>Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}</span>
          <label className="inline-flex items-center gap-1">
            <span>Rows:</span>
            <select
              value={String(table.getState().pagination.pageSize)}
              onChange={(e) => {
                const v = e.target.value;
                if (v === 'all') {
                  table.setPageSize(table.getPrePaginationRowModel().rows.length);
                } else {
                  table.setPageSize(Number(v));
                }
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
        <button onClick={() => table.nextPage()} disabled={!table.getCanNextPage()} className="px-2 py-1 border rounded-md disabled:opacity-50">Next</button>
      </div>

      {showModal && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <form
            onSubmit={handleCreate}
            className="space-y-2 rounded bg-white p-4 shadow"
          >
            <h2 className="text-lg font-semibold">
              {editingId ? 'Edit Expense' : 'Add Expense'}
            </h2>
            <input
              aria-label="description"
              className="w-full border p-2"
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              placeholder="Description"
              required
            />
            <input
              aria-label="amount"
              className="w-full border p-2"
              type="number"
              step="0.01"
              value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })}
              placeholder="Amount"
              required
            />
            <input
              aria-label="date"
              className="w-full border p-2"
              type="date"
              value={form.date}
              onChange={(e) => setForm({ ...form, date: e.target.value })}
              disabled={!!editingId}
              required
            />
            {editingId && (
              <p className="text-xs text-gray-600">
                Editing date is temporarily unavailable.
              </p>
            )}
            <input
              aria-label="category"
              className="w-full border p-2"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              placeholder="Category"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2"
                onClick={() => { setShowModal(false); setEditingId(null); }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="bg-blue-600 px-4 py-2 text-white"
              >
                {editingId ? 'Save Changes' : 'Save'}
              </button>
            </div>
          </form>
        </div>
      )}

      {viewItem && (
        <div className="fixed inset-0 bg-black/30 flex" role="dialog" aria-modal>
          <aside className="ml-auto h-full w-full max-w-md bg-white shadow-xl p-4 flex flex-col gap-2">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-lg font-semibold">Expense Details</h2>
              <button className="px-2 py-1 border rounded-md" onClick={() => setViewItem(null)} aria-label="Close">Close</button>
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span className="text-gray-600">Date</span><span>{viewItem.date}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Description</span><span>{viewItem.description}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Category</span><span>{viewItem.category ?? '-'}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Amount</span><span className="tabular-nums">${viewItem.amount.toFixed(2)}</span></div>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
