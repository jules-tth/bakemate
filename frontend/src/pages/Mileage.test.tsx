import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import * as mileageApi from '../api/mileage';
import Mileage from './Mileage';

vi.mock('../api/mileage');

describe('Mileage page', () => {
  it('creates mileage log via form', async () => {
    vi.mocked(mileageApi.listMileageLogs).mockResolvedValue([]);
    vi.mocked(mileageApi.createMileageLog).mockResolvedValue({
      id: '1',
      date: '2024-01-01',
      distance: 5,
      description: 'Delivery',
      reimbursement: 2.5
    });

    render(
      <AuthProvider>
        <MemoryRouter>
          <Mileage />
        </MemoryRouter>
      </AuthProvider>
    );

    fireEvent.click(screen.getByText(/add log/i));
    fireEvent.change(screen.getByLabelText('date'), {
      target: { value: '2024-01-01' }
    });
    fireEvent.change(screen.getByLabelText('distance'), {
      target: { value: '5' }
    });
    fireEvent.change(screen.getByLabelText('description'), {
      target: { value: 'Delivery' }
    });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    expect(mileageApi.createMileageLog).toHaveBeenCalledWith({
      date: '2024-01-01',
      distance: 5,
      description: 'Delivery'
    });
  });
});

