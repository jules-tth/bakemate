import apiClient from './index';

export interface Task {
  id: string;
  title: string;
  status: string;
  due_date?: string;
}

export async function listTasks(): Promise<Task[]> {
  const response = await apiClient.get<Task[]>('/tasks');
  return response.data;
}

export async function createTask(task: Omit<Task, 'id'>): Promise<Task> {
  const response = await apiClient.post<Task>('/tasks', task);
  return response.data;
}

export async function updateTask(id: string, task: Partial<Task>): Promise<Task> {
  const response = await apiClient.put<Task>(`/tasks/${id}`, task);
  return response.data;
}

export async function deleteTask(id: string): Promise<void> {
  await apiClient.delete(`/tasks/${id}`);
}
