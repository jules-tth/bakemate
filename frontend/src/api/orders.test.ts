import { describe, expect, it, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import apiClient from './index';
import { getOrders, getOrdersSummary, OrdersQuery } from './orders';

describe('orders API', () => {
  it('fetches orders list with params', async () => {
    const params: OrdersQuery = {
      start: '2025-01-01',
      end: '2025-01-31',
      status: 'Open',
      page: 1,
      pageSize: 25,
    };
    const backendOrders = [
      {
        id: '1',
        order_number: 'A1',
        customer_name: 'John',
        event_type: 'Birthday',
        status: 'confirmed',
        order_date: '2025-01-05',
        due_date: '2025-01-10',
        delivery_method: 'Pickup',
        total_amount: 100,
      },
    ];
    const spy = vi
      .spyOn(apiClient, 'get')
      .mockResolvedValue({ data: backendOrders } as AxiosResponse<typeof backendOrders>);

    const result = await getOrders(params);
    expect(spy).toHaveBeenCalledWith('/orders', {
      params: { skip: 0, limit: 200, status: 'Open' },
    });
    expect(result).toEqual({
      rows: [
        {
          id: '1',
          orderNo: 'A1',
          customer: 'John',
          event: 'Birthday',
          status: 'confirmed',
          paymentStatus: undefined,
          orderDate: '2025-01-05',
          dueDate: '2025-01-10',
          deliveryMethod: 'Pickup',
          total: 100,
          subtotal: undefined,
          tax: undefined,
          balanceDue: null,
          depositAmount: null,
          depositDueDate: null,
          balanceDueDate: null,
          notesToCustomer: null,
          internalNotes: null,
          createdAt: undefined,
          updatedAt: undefined,
          priority: 'Normal',
        },
      ],
      page: 1,
      pageSize: 1,
      total: 1,
    });
    spy.mockRestore();
  });

  it('fetches orders summary', async () => {
    const ordersData = [{ date: 'Jan', count: 1 }];
    const revenueData = [{ date: 'Jan', revenue: 100 }];
    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce(
      { data: ordersData } as AxiosResponse<typeof ordersData>,
    ).mockResolvedValueOnce(
      { data: revenueData } as AxiosResponse<typeof revenueData>,
    );

    const result = await getOrdersSummary('2025');
    expect(spy).toHaveBeenNthCalledWith(1, '/dashboard/orders', {
      params: { range: '2025' },
    });
    expect(spy).toHaveBeenNthCalledWith(2, '/dashboard/revenue', {
      params: { range: '2025' },
    });
    expect(result).toEqual({
      series: [{ date: 'Jan', orders: 1, revenue: 100 }],
      totals: { orders: 1, revenue: 100 },
    });
    spy.mockRestore();
  });
});

