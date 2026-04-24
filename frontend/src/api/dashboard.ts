import apiClient from './index';

export interface DashboardSummary {
  revenue: number;
  total_orders: number;
  ingredients_low: number;
}

export interface OrdersOverTime {
  date: string;
  count: number;
}

export interface RevenueOverTime {
  date: string;
  revenue: number;
}

export async function getDashboardSummary(range: string): Promise<DashboardSummary> {
  const response = await apiClient.get<DashboardSummary>('/dashboard/summary', {
    params: { range },
  });
  return response.data;
}

export async function getOrdersOverTime(range: string): Promise<OrdersOverTime[]> {
  const response = await apiClient.get<OrdersOverTime[]>('/dashboard/orders', {
    params: { range },
  });
  return response.data;
}

export async function getRevenueOverTime(range: string): Promise<RevenueOverTime[]> {
  const response = await apiClient.get<RevenueOverTime[]>('/dashboard/revenue', {
    params: { range },
  });
  return response.data;
}

