import apiClient from './index';

export interface CalendarEvent {
  id: string;
  title: string;
  start_datetime: string;
  end_datetime: string;
}

export async function listCalendarEvents(): Promise<CalendarEvent[]> {
  const response = await apiClient.get<CalendarEvent[]>('/calendar');
  return response.data;
}

export async function createCalendarEvent(event: Omit<CalendarEvent, 'id'>): Promise<CalendarEvent> {
  const response = await apiClient.post<CalendarEvent>('/calendar', event);
  return response.data;
}

export async function updateCalendarEvent(id: string, event: Partial<CalendarEvent>): Promise<CalendarEvent> {
  const response = await apiClient.put<CalendarEvent>(`/calendar/${id}`, event);
  return response.data;
}

export async function deleteCalendarEvent(id: string): Promise<void> {
  await apiClient.delete(`/calendar/${id}`);
}
