import apiClient from './index';

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/users/users/me');
  return response.data;
}

