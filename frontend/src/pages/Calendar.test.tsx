import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import * as taskApi from '../api/tasks';
import * as calendarApi from '../api/calendar';
import Calendar from './Calendar';

vi.mock('../api/tasks');
vi.mock('../api/calendar');

describe('Calendar page', () => {
  it('creates task via form', async () => {
    vi.mocked(taskApi.listTasks).mockResolvedValue([]);
    vi.mocked(taskApi.createTask).mockResolvedValue({
      id: '1',
      title: 'New Task',
      status: 'pending',
    });
    vi.mocked(calendarApi.listCalendarEvents).mockResolvedValue([]);

    render(
      <AuthProvider>
        <MemoryRouter>
          <Calendar />
        </MemoryRouter>
      </AuthProvider>
    );

    fireEvent.change(screen.getByLabelText(/task title/i), {
      target: { value: 'New Task' },
    });
    fireEvent.click(screen.getByRole('button', { name: /add task/i }));

    expect(taskApi.createTask).toHaveBeenCalledWith({ title: 'New Task', status: 'pending' });
  });
});
