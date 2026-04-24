import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import IncomeStatement from './IncomeStatement';
import * as reportsApi from '../../api/reports';
import * as exportUtil from '../../utils/export';

vi.mock('../../api/reports');
vi.mock('../../utils/export');

describe('IncomeStatement report', () => {
  it('previews data and exports PDF', async () => {
    vi.setSystemTime(new Date('2024-06-15'));
    vi.mocked(reportsApi.getProfitAndLoss).mockResolvedValue({
      total_revenue: 100,
      cost_of_goods_sold: 40,
      gross_profit: 60,
      operating_expenses: { total: 20, by_category: { Rent: 10, Utilities: 10 } },
      net_profit: 40,
    });
    vi.mocked(exportUtil.exportElementPDF).mockResolvedValue();

    render(
      <AuthProvider>
        <MemoryRouter>
          <IncomeStatement />
        </MemoryRouter>
      </AuthProvider>
    );

    await screen.findByText(/Income Statement \(2024\)/);
    expect(reportsApi.getProfitAndLoss).toHaveBeenCalledWith('2024-01-01', '2024-12-31');
    expect(screen.getByText('Rent')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /export pdf/i }));
    expect(exportUtil.exportElementPDF).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      'Income Statement — 2024',
      'income-statement.pdf'
    );
    vi.useRealTimers();
  });
});

