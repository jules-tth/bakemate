import type { Order } from '../api/orders';

interface Props {
  order: Order | null;
  onClose: () => void;
}

export default function OrderDetailDrawer({ order, onClose }: Props) {
  if (!order) return null;
  return (
    <div className="fixed inset-0 flex justify-end bg-black/30" role="dialog">
      <div className="w-80 bg-white h-full p-4 shadow-xl">
        <button onClick={onClose} className="mb-4 text-sm text-blue-600">
          Close
        </button>
        <h3 className="text-lg font-medium mb-4">Order {order.orderNo}</h3>
        <dl className="text-sm space-y-2">
          <div>
            <dt className="font-medium">Customer</dt>
            <dd>{order.customer}</dd>
          </div>
          <div>
            <dt className="font-medium">Event</dt>
            <dd>{order.event}</dd>
          </div>
          <div>
            <dt className="font-medium">Status</dt>
            <dd>{order.status}</dd>
          </div>
          <div>
            <dt className="font-medium">Due</dt>
            <dd>{order.dueDate}</dd>
          </div>
          <div>
            <dt className="font-medium">Total</dt>
            <dd>${order.total}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}

