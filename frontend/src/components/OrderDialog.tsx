import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { useState } from 'react';
import type { Order } from '../api/orders';

// Use backend enum values for status to ensure compatibility
const ORDER_STATUS = [
  'inquiry',
  'quote_sent',
  'confirmed',
  'in_progress',
  'ready_for_pickup',
  'completed',
  'cancelled',
] as const;

const schema = z.object({
  customer: z.string().optional().default(''),
  event: z.string().optional().default(''),
  orderDate: z.string().min(1),
  dueDate: z.string().min(1),
  deliveryMethod: z.string().optional().default(''),
  status: z.enum(ORDER_STATUS).default('inquiry'),
  notesToCustomer: z.string().optional().default(''),
  internalNotes: z.string().optional().default(''),
  depositAmount: z.coerce.number().optional().nullable(),
  depositDueDate: z.string().optional().nullable(),
  balanceDueDate: z.string().optional().nullable(),
  total: z.coerce.number().nonnegative().optional().default(0),
});

export type OrderFormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  order?: Order;
  onClose: () => void;
  onSubmit: (data: OrderFormData) => void;
}

export default function OrderDialog({ open, order, onClose, onSubmit }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<OrderFormData>({
    resolver: zodResolver(schema),
    defaultValues: order
      ? {
          customer: order.customer,
          event: order.event,
          orderDate: order.orderDate?.slice(0, 10) ?? '',
          dueDate: order.dueDate?.slice(0, 10) ?? '',
          deliveryMethod: order.deliveryMethod ?? '',
          status: (ORDER_STATUS.includes(order.status as typeof ORDER_STATUS[number])
            ? (order.status as typeof ORDER_STATUS[number])
            : 'inquiry'),
          notesToCustomer: order.notesToCustomer ?? '',
          internalNotes: order.internalNotes ?? '',
          depositAmount: order.depositAmount ?? undefined,
          depositDueDate: order.depositDueDate ?? undefined,
          balanceDueDate: order.balanceDueDate ?? undefined,
          total: order.total ?? 0,
        }
      : undefined,
  });
  const [submitting, setSubmitting] = useState(false);

  const submit = handleSubmit(async (data) => {
    setSubmitting(true);
    await onSubmit(data);
    setSubmitting(false);
    onClose();
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center" role="dialog">
      <form
        onSubmit={submit}
        className="bg-white p-4 rounded-md w-80 space-y-2"
      >
        <h3 className="text-lg font-medium mb-2">
          {order ? 'Edit Order' : 'Add Order'}
        </h3>
        <input
          {...register('customer')}
          placeholder="Customer"
          className="w-full border p-2 rounded"
        />
        {errors.customer && (
          <span className="text-red-600 text-sm">Customer required</span>
        )}
        <input
          {...register('event')}
          placeholder="Event"
          className="w-full border p-2 rounded"
        />
        <input
          type="date"
          {...register('orderDate')}
          className="w-full border p-2 rounded"
        />
        <input
          type="date"
          {...register('dueDate')}
          className="w-full border p-2 rounded"
        />
        <input
          {...register('deliveryMethod')}
          placeholder="Delivery Method"
          className="w-full border p-2 rounded"
        />
        <label className="text-xs text-gray-600">Status</label>
        <select {...register('status')} className="w-full border p-2 rounded">
          {ORDER_STATUS.map((s) => (
            <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <textarea
          {...register('notesToCustomer')}
          placeholder="Notes to customer"
          className="w-full border p-2 rounded"
          rows={2}
        />
        <textarea
          {...register('internalNotes')}
          placeholder="Internal notes"
          className="w-full border p-2 rounded"
          rows={2}
        />
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-gray-600">Deposit Amount</label>
            <input
              type="number"
              step="0.01"
              {...register('depositAmount')}
              placeholder="0.00"
              className="w-full border p-2 rounded"
            />
          </div>
          <div>
            <label className="text-xs text-gray-600">Deposit Due Date</label>
            <input
              type="date"
              {...register('depositDueDate')}
              className="w-full border p-2 rounded"
            />
          </div>
          <div>
            <label className="text-xs text-gray-600">Balance Due Date</label>
            <input
              type="date"
              {...register('balanceDueDate')}
              className="w-full border p-2 rounded"
            />
          </div>
          <div>
            <label className="text-xs text-gray-600">Total</label>
            <input
              type="number"
              step="0.01"
              {...register('total')}
              placeholder="0.00"
              className="w-full border p-2 rounded"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button type="button" onClick={onClose} className="px-3 py-1 border rounded-md">
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-3 py-1 bg-blue-600 text-white rounded-md"
          >
            Save
          </button>
        </div>
      </form>
    </div>
  );
}
