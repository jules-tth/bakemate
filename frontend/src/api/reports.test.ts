import { describe, expect, it, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import apiClient from './index';
import { getProfitAndLoss, ProfitAndLoss } from './reports';

describe('getProfitAndLoss', () => {
  it('requests profit and loss report with dates', async () => {
    const data: ProfitAndLoss = {
      total_revenue: 100,
      cost_of_goods_sold: 40,
      gross_profit: 60,
      operating_expenses: { total: 10, by_category: { rent: 10 } },
      net_profit: 50
    };
    const getSpy = vi
      .spyOn(apiClient, 'get')
      .mockResolvedValue({ data } as AxiosResponse<ProfitAndLoss>);

    const result = await getProfitAndLoss('2024-01-01', '2024-01-31');
    expect(getSpy).toHaveBeenCalledWith('/reports/profit-and-loss', {
      params: { start_date: '2024-01-01', end_date: '2024-01-31' }
    });
    expect(result).toEqual(data);
    getSpy.mockRestore();
  });
});

