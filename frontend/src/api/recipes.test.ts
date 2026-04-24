import { describe, expect, it, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import apiClient from './index';
import { listRecipes, Recipe } from './recipes';

describe('listRecipes', () => {
  it('fetches recipes from API', async () => {
    const data: Recipe[] = [{ id: '1', name: 'Cake', description: 'Yummy' }];
    const getSpy = vi
      .spyOn(apiClient, 'get')
      .mockResolvedValue({ data } as AxiosResponse<Recipe[]>);

    const result = await listRecipes();
    expect(getSpy).toHaveBeenCalledWith('/recipes');
    expect(result).toEqual(data);
    getSpy.mockRestore();
  });
});
