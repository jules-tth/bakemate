import { describe, expect, it, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import apiClient from './index';
import { listIngredients, Ingredient } from './ingredients';

describe('listIngredients', () => {
  it('fetches ingredients from API', async () => {
    const data: Ingredient[] = [
      { id: '1', name: 'Flour', unit: 'kg', cost: 2.5 }
    ];
    const getSpy = vi
      .spyOn(apiClient, 'get')
      .mockResolvedValue({ data } as AxiosResponse<Ingredient[]>);

    const result = await listIngredients();
    expect(getSpy).toHaveBeenCalledWith('/ingredients');
    expect(result).toEqual(data);
    getSpy.mockRestore();
  });
});
