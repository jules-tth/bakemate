import { OrderDetailEntry } from '@/components/order-detail-entry';

export default async function OrderDetailPage({ params }: { params: Promise<{ orderId: string }> }) {
  const { orderId } = await params;
  return <OrderDetailEntry orderId={orderId} />;
}
