import apiClient from './index';

export interface PricingConfig {
  id: string;
  user_id: string;
  hourly_rate: number;
  overhead_per_month: number;
  created_at: string;
  updated_at: string;
}

export type PricingConfigInput = {
  hourly_rate: number;
  overhead_per_month: number;
};

export async function getPricingConfig(): Promise<PricingConfig> {
  const response = await apiClient.get<PricingConfig>('/pricing/configuration');
  return response.data;
}

export async function savePricingConfig(
  config: PricingConfigInput
): Promise<PricingConfig> {
  const response = await apiClient.post<PricingConfig>(
    '/pricing/configuration',
    config
  );
  return response.data;
}

