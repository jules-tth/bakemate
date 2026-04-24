import apiClient from './index';

export interface ProfitAndLoss {
  total_revenue: number;
  cost_of_goods_sold: number;
  gross_profit: number;
  operating_expenses: {
    total: number;
    by_category: Record<string, number>;
  };
  net_profit: number;
}

export async function getProfitAndLoss(
  start_date: string,
  end_date: string
): Promise<ProfitAndLoss> {
  const response = await apiClient.get<ProfitAndLoss>(
    '/reports/profit-and-loss',
    { params: { start_date, end_date } }
  );
  return response.data;
}

