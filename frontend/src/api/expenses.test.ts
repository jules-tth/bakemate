import { describe, expect, it, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import apiClient from './index';
import { listExpenses, Expense } from './expenses';

describe('listExpenses', () => {
  it('fetches expenses from API', async () => {
    const data: Expense[] = [
      { id: '1', description: 'Supplies', amount: 10, date: '2024-01-01' }
    ];
    const getSpy = vi
      .spyOn(apiClient, 'get')
      .mockResolvedValue({ data } as AxiosResponse<Expense[]>);

    const result = await listExpenses();
    expect(getSpy).toHaveBeenCalledWith('/expenses', {
      params: { skip: 0, limit: 200 },
    });
    expect(result).toEqual(data);
    getSpy.mockRestore();
  });
});

