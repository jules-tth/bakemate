import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';
import type { SortingState, VisibilityState, Row } from '@tanstack/react-table';
import { useMemo, useState } from 'react';
import { format } from 'date-fns';
import type { Order } from '../api/orders';

interface Props {
  data: Order[];
  onRowClick?: (order: Order) => void;
  onEdit?: (order: Order) => void;
  onView?: (order: Order) => void;
  onCancel?: (order: Order) => void;
  onDelete?: (order: Order) => void;
}

export default function OrdersTable({ data, onRowClick, onEdit, onView, onCancel, onDelete }: Props) {
  // Default sort by Order # descending (latest first)
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'orderNo', desc: true },
  ]);
  const [pageSizeAll, setPageSizeAll] = useState(false);
  const [columnsOpen, setColumnsOpen] = useState(false);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({
    deliveryMethod: false, // hide method by default
    subtotal: false,
    tax: false,
    balanceDue: false,
    depositAmount: false,
    depositDueDate: false,
    balanceDueDate: false,
    notesToCustomer: false,
    internalNotes: false,
    createdAt: false,
    updatedAt: false,
  });

  const currency = useMemo(
    () => new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }),
    []
  );
  const columns = [
    // Defaults: Order #, Date (order_date), Delivery (due_date), Status, Customer, Event, Payment, Total
    { header: 'Order #', accessorKey: 'orderNo' },
    {
      header: 'Date',
      accessorKey: 'orderDate',
      cell: ({ getValue }: { getValue: () => string }) =>
        format(new Date(getValue()), 'yyyy-MM-dd'),
    },
    {
      header: 'Delivery',
      accessorKey: 'dueDate',
      cell: ({ getValue }: { getValue: () => string }) =>
        format(new Date(getValue()), 'yyyy-MM-dd'),
    },
    {
      header: 'Status',
      accessorKey: 'status',
      cell: ({ getValue }: { getValue: () => string }) => {
        const raw = getValue();
        const label = raw.replace(/_/g, ' ');
        const cls = (() => {
          switch (raw) {
            case 'inquiry':
              return 'bg-gray-100 text-gray-800';
            case 'quote_sent':
              return 'bg-indigo-100 text-indigo-800';
            case 'confirmed':
              return 'bg-blue-100 text-blue-800';
            case 'in_progress':
              return 'bg-amber-100 text-amber-800';
            case 'ready_for_pickup':
              return 'bg-teal-100 text-teal-800';
            case 'completed':
              return 'bg-green-100 text-green-800';
            case 'cancelled':
              return 'bg-rose-100 text-rose-800';
            default:
              return 'bg-slate-100 text-slate-800';
          }
        })();
        return (
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
            {label}
          </span>
        );
      },
    },
    { header: 'Customer', accessorKey: 'customer' },
    { header: 'Event', accessorKey: 'event' },
    {
      header: 'Payment',
      accessorKey: 'paymentStatus',
      cell: ({ getValue }: { getValue: () => string | undefined }) => {
        const raw = (getValue() ?? '').toLowerCase();
        const label = raw || '-';
        const cls = (() => {
          switch (raw) {
            case 'paid':
              return 'bg-green-100 text-green-800';
            case 'partial':
              return 'bg-amber-100 text-amber-800';
            case 'unpaid':
              return 'bg-rose-100 text-rose-800';
            default:
              return 'bg-slate-100 text-slate-800';
          }
        })();
        return (
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
            {label}
          </span>
        );
      },
    },
    {
      header: 'Total',
      accessorKey: 'total',
      cell: ({ getValue }: { getValue: () => number }) => (
        <span className="tabular-nums">{currency.format(getValue())}</span>
      ),
    },
    // Extended (hidden by default unless toggled)
    { header: 'Delivery Method', accessorKey: 'deliveryMethod' },
    {
      header: 'Subtotal',
      accessorKey: 'subtotal',
      cell: ({ getValue }: { getValue: () => number | undefined }) =>
        getValue() !== undefined ? (
          <span className="tabular-nums">{currency.format(getValue() ?? 0)}</span>
        ) : null,
    },
    {
      header: 'Tax',
      accessorKey: 'tax',
      cell: ({ getValue }: { getValue: () => number | undefined }) =>
        getValue() !== undefined ? (
          <span className="tabular-nums">{currency.format(getValue() ?? 0)}</span>
        ) : null,
    },
    {
      header: 'Balance Due',
      accessorKey: 'balanceDue',
      cell: ({ getValue }: { getValue: () => number | null }) =>
        getValue() != null ? (
          <span className="tabular-nums">{currency.format(getValue() ?? 0)}</span>
        ) : null,
    },
    {
      header: 'Deposit',
      accessorKey: 'depositAmount',
      cell: ({ getValue }: { getValue: () => number | null }) =>
        getValue() != null ? (
          <span className="tabular-nums">{currency.format(getValue() ?? 0)}</span>
        ) : null,
    },
    {
      header: 'Deposit Due',
      accessorKey: 'depositDueDate',
      cell: ({ getValue }: { getValue: () => string | null }) =>
        getValue() ? format(new Date(String(getValue())), 'yyyy-MM-dd') : null,
    },
    {
      header: 'Balance Due Date',
      accessorKey: 'balanceDueDate',
      cell: ({ getValue }: { getValue: () => string | null }) =>
        getValue() ? format(new Date(String(getValue())), 'yyyy-MM-dd') : null,
    },
    { header: 'Notes to Customer', accessorKey: 'notesToCustomer' },
    { header: 'Internal Notes', accessorKey: 'internalNotes' },
    {
      header: 'Created',
      accessorKey: 'createdAt',
      cell: ({ getValue }: { getValue: () => string | undefined }) =>
        getValue() ? format(new Date(String(getValue())), 'yyyy-MM-dd') : null,
    },
    {
      header: 'Updated',
      accessorKey: 'updatedAt',
      cell: ({ getValue }: { getValue: () => string | undefined }) =>
        getValue() ? format(new Date(String(getValue())), 'yyyy-MM-dd') : null,
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }: { row: Row<Order> }) => (
        <details className="relative">
          <summary className="list-none cursor-pointer select-none px-2 py-1 border rounded-md text-xs inline-flex items-center gap-1">
            Actions
            <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path d="M5.25 7.5L10 12.25L14.75 7.5H5.25Z"/></svg>
          </summary>
          <div className="absolute z-10 mt-1 w-40 bg-white border rounded-md shadow">
            <button className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50" onClick={() => onEdit?.(row.original)}>Edit Order</button>
            <button className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50" onClick={() => onView?.(row.original)}>View Order</button>
            <button className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50" onClick={() => onCancel?.(row.original)}>Cancel Order</button>
            <button className="w-full text-left px-3 py-2 text-sm text-rose-700 hover:bg-rose-50" onClick={() => onDelete?.(row.original)}>Delete Order</button>
          </div>
        </details>
      ),
    },
  ];

  const table = useReactTable({
    data,
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
    <div className="bg-white rounded-2xl shadow">
      <div className="flex justify-end p-2">
        <div className="relative">
          <button
            className="px-2 py-1 border rounded-md text-sm"
            onClick={() => setColumnsOpen((o) => !o)}
            aria-expanded={columnsOpen}
            aria-controls="orders-columns-menu"
          >
            Columns
          </button>
          {columnsOpen && (
            <div
              id="orders-columns-menu"
              className="absolute right-0 mt-2 w-56 bg-white border rounded-md shadow p-2 z-10"
            >
              <p className="px-1 pb-1 text-xs text-gray-500">Toggle columns</p>
              <div className="max-h-60 overflow-auto">
                {table.getAllLeafColumns().map((col) => (
                  <label key={col.id} className="flex items-center gap-2 px-1 py-1 text-sm">
                    <input
                      type="checkbox"
                      checked={col.getIsVisible()}
                      onChange={col.getToggleVisibilityHandler()}
                    />
                    <span>{String(col.columnDef.header)}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      <table
        className="w-full text-sm border border-gray-200"
        role="grid"
        id="orders-table"
      >
        <thead className="bg-gray-50">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-3 py-2 text-left cursor-pointer border-b"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className="odd:bg-white even:bg-gray-50 cursor-pointer"
              onClick={() => onRowClick?.(row.original)}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-3 py-2 border-b">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex justify-between items-center gap-4 p-2 text-sm">
        <button
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
          className="px-2 py-1 border rounded-md disabled:opacity-50"
        >
          Prev
        </button>
        <div className="flex items-center gap-2">
          <span>
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </span>
          <label className="inline-flex items-center gap-1">
            <span>Rows:</span>
            <select
              value={pageSizeAll ? 'all' : String(table.getState().pagination.pageSize)}
              onChange={(e) => {
                const v = e.target.value;
                if (v === 'all') {
                  setPageSizeAll(true);
                  table.setPageSize(table.getPrePaginationRowModel().rows.length);
                } else {
                  setPageSizeAll(false);
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
        <button
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
          className="px-2 py-1 border rounded-md disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}
