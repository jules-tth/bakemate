import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import Pricing from './Pricing';
import * as api from '../api/pricing';

describe('Pricing page', () => {
  it('updates pricing configuration', async () => {
    const getSpy = vi
      .spyOn(api, 'getPricingConfig')
      .mockResolvedValue({
        id: '1',
        user_id: 'u1',
        hourly_rate: 25,
        overhead_per_month: 100,
        created_at: '',
        updated_at: ''
      });
    const saveSpy = vi
      .spyOn(api, 'savePricingConfig')
      .mockResolvedValue({
        id: '1',
        user_id: 'u1',
        hourly_rate: 30,
        overhead_per_month: 200,
        created_at: '',
        updated_at: ''
      });

    render(
      <AuthProvider>
        <MemoryRouter>
          <Pricing />
        </MemoryRouter>
      </AuthProvider>
    );

    // Wait for initial fetch
    await screen.findByLabelText('hourly_rate');

    fireEvent.change(screen.getByLabelText('hourly_rate'), {
      target: { value: '30' }
    });
    fireEvent.change(screen.getByLabelText('overhead_per_month'), {
      target: { value: '200' }
    });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    expect(saveSpy).toHaveBeenCalledWith({
      hourly_rate: 30,
      overhead_per_month: 200
    });

    saveSpy.mockRestore();
    getSpy.mockRestore();
  });
});
