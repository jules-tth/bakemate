import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import OrdersTable from './OrdersTable';
import type { Order } from '../api/orders';

const sampleData: Order[] = [
  {
    id: '1',
    orderNo: '1001',
    customer: 'Alice',
    event: 'Birthday',
    status: 'Open',
    orderDate: '2025-02-01',
    dueDate: '2025-03-01',
    deliveryMethod: 'Pickup',
    total: 100,
    priority: 'Low',
  },
];

describe('OrdersTable', () => {
  it('renders rows and handles click', () => {
    const onRowClick = vi.fn();
    render(<OrdersTable data={sampleData} onRowClick={onRowClick} />);
    expect(screen.getByText('1001')).toBeInTheDocument();
    fireEvent.click(screen.getByText('1001'));
    expect(onRowClick).toHaveBeenCalledWith(sampleData[0]);
  });
});
