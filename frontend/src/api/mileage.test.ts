import { describe, expect, it, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import apiClient from './index';
import { listMileageLogs, MileageLog } from './mileage';

describe('listMileageLogs', () => {
  it('fetches mileage logs from API', async () => {
    const data: MileageLog[] = [
      { id: '1', date: '2024-01-01', distance: 5, reimbursement: 2.5 }
    ];
    const getSpy = vi
      .spyOn(apiClient, 'get')
      .mockResolvedValue({ data } as AxiosResponse<MileageLog[]>);

    const result = await listMileageLogs();
    expect(getSpy).toHaveBeenCalledWith('/mileage', {
      params: { skip: 0, limit: 200 },
    });
    expect(result).toEqual(data);
    getSpy.mockRestore();
  });
});

