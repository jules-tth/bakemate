import { describe, expect, it, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import apiClient from './index';
import { getCurrentUser, User } from './users';

describe('getCurrentUser', () => {
  it('fetches the current user from API', async () => {
    const data: User = {
      id: '1',
      email: 'test@example.com',
      is_active: true,
      is_superuser: false,
    };
    const getSpy = vi
      .spyOn(apiClient, 'get')
      .mockResolvedValue({ data } as AxiosResponse<User>);

    const result = await getCurrentUser();

    expect(getSpy).toHaveBeenCalledWith('/users/users/me');
    expect(result).toEqual(data);
    getSpy.mockRestore();
  });
});

