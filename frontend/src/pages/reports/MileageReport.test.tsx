import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import MileageReport from './MileageReport';
import * as mileageApi from '../../api/mileage';
import * as exportUtil from '../../utils/export';

vi.mock('../../api/mileage');
vi.mock('../../utils/export');

describe('Mileage report', () => {
  it('previews data and exports PDF', async () => {
    vi.setSystemTime(new Date('2024-06-15'));
    vi.mocked(mileageApi.listMileageLogs).mockResolvedValue([
      { id: '1', date: '2024-01-01', distance: 10, reimbursement: 5, description: 'Trip' }
    ]);
    vi.mocked(exportUtil.exportElementPDF).mockResolvedValue();

    render(
      <AuthProvider>
        <MemoryRouter>
          <MileageReport />
        </MemoryRouter>
      </AuthProvider>
    );

    await screen.findByText(/Mileage \(2024\)/);
    expect(mileageApi.listMileageLogs).toHaveBeenCalledWith({ start_date: '2024-01-01', end_date: '2024-12-31' });
    expect(screen.getByText('Trip')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /export pdf/i }));
    expect(exportUtil.exportElementPDF).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      'Mileage — 2024',
      'mileage-report.pdf'
    );
    vi.useRealTimers();
  });
});

