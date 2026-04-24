import { describe, expect, it, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import apiClient from './index';
import { getPricingConfig, savePricingConfig, PricingConfig } from './pricing';

describe('pricing api', () => {
  it('fetches pricing configuration', async () => {
    const data: PricingConfig = {
      id: '1',
      user_id: 'u1',
      hourly_rate: 25,
      overhead_per_month: 100,
      created_at: '',
      updated_at: ''
    };
    const getSpy = vi
      .spyOn(apiClient, 'get')
      .mockResolvedValue({ data } as AxiosResponse<PricingConfig>);

    const result = await getPricingConfig();
    expect(getSpy).toHaveBeenCalledWith('/pricing/configuration');
    expect(result).toEqual(data);
    getSpy.mockRestore();
  });

  it('saves pricing configuration', async () => {
    const data: PricingConfig = {
      id: '1',
      user_id: 'u1',
      hourly_rate: 30,
      overhead_per_month: 200,
      created_at: '',
      updated_at: ''
    };
    const postSpy = vi
      .spyOn(apiClient, 'post')
      .mockResolvedValue({ data } as AxiosResponse<PricingConfig>);

    const result = await savePricingConfig({ hourly_rate: 30, overhead_per_month: 200 });
    expect(postSpy).toHaveBeenCalledWith('/pricing/configuration', {
      hourly_rate: 30,
      overhead_per_month: 200
    });
    expect(result).toEqual(data);
    postSpy.mockRestore();
  });
});
