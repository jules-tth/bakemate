import apiClient from './index';

export interface MileageLog {
  id: string;
  date: string;
  distance: number;
  description?: string;
  reimbursement: number;
}

export type MileageInput = Omit<MileageLog, 'id' | 'reimbursement'>;

export async function listMileageLogs(params?: {
  start_date?: string;
  end_date?: string;
}): Promise<MileageLog[]> {
  const all: MileageLog[] = [];
  const limit = 200;
  let skip = 0;
  while (true) {
    const response = await apiClient.get<MileageLog[]>(
      '/mileage',
      { params: { skip, limit, ...(params ?? {}) } },
    );
    const batch = response.data;
    if (!batch.length) break;
    all.push(...batch);
    if (batch.length < limit) break;
    skip += limit;
  }
  return all;
}

export async function createMileageLog(log: MileageInput): Promise<MileageLog> {
  const response = await apiClient.post<MileageLog>('/mileage', log);
  return response.data;
}

export async function updateMileageLog(
  id: string,
  log: Partial<MileageInput>
): Promise<MileageLog> {
  const response = await apiClient.put<MileageLog>(`/mileage/${id}`, log);
  return response.data;
}

export async function deleteMileageLog(id: string): Promise<void> {
  await apiClient.delete(`/mileage/${id}`);
}
