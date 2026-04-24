import { describe, expect, it, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import apiClient from './index';
import { listCalendarEvents, CalendarEvent } from './calendar';

describe('listCalendarEvents', () => {
  it('fetches calendar events from API', async () => {
    const data: CalendarEvent[] = [
      { id: '1', title: 'Event', start_datetime: '2024-01-01', end_datetime: '2024-01-01' },
    ];
    const getSpy = vi
      .spyOn(apiClient, 'get')
      .mockResolvedValue({ data } as AxiosResponse<CalendarEvent[]>);

    const result = await listCalendarEvents();
    expect(getSpy).toHaveBeenCalledWith('/calendar');
    expect(result).toEqual(data);
    getSpy.mockRestore();
  });
});
