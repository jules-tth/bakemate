import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import Dashboard from './Dashboard';
import * as api from '../api/dashboard';

import { setupResizeObserverMock } from '../testUtils/resizeObserverMock';

beforeAll(() => {
  setupResizeObserverMock();
});

describe('Dashboard page', () => {
  it('loads metrics and refetches on date change', async () => {
    const summarySpy = vi
      .spyOn(api, 'getDashboardSummary')
      .mockResolvedValue({ revenue: 5417, total_orders: 172, ingredients_low: 3 });
    const ordersSpy = vi
      .spyOn(api, 'getOrdersOverTime')
      .mockResolvedValue([{ date: 'Jan', count: 5 }]);
    const revenueSpy = vi
      .spyOn(api, 'getRevenueOverTime')
      .mockResolvedValue([{ date: 'Jan', revenue: 1000 }]);

    render(<Dashboard />);

    await waitFor(() => expect(summarySpy).toHaveBeenCalledWith('YTD'));
    expect(screen.getByText('$5,417')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/date range/i), {
      target: { value: '2024' },
    });

    await waitFor(() => expect(summarySpy).toHaveBeenLastCalledWith('2024'));

    summarySpy.mockRestore();
    ordersSpy.mockRestore();
    revenueSpy.mockRestore();
  });
});

