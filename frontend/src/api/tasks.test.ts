import { describe, expect, it, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import apiClient from './index';
import { listTasks, Task } from './tasks';

describe('listTasks', () => {
  it('fetches tasks from API', async () => {
    const data: Task[] = [{ id: '1', title: 'Task', status: 'pending' }];
    const getSpy = vi
      .spyOn(apiClient, 'get')
      .mockResolvedValue({ data } as AxiosResponse<Task[]>);

    const result = await listTasks();
    expect(getSpy).toHaveBeenCalledWith('/tasks');
    expect(result).toEqual(data);
    getSpy.mockRestore();
  });
});
