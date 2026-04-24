import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import Ingredients from './Ingredients';
import * as api from '../api/ingredients';

describe('Ingredients page', () => {
  it('creates ingredient via form', async () => {
    const listSpy = vi.spyOn(api, 'listIngredients').mockResolvedValue([]);
    const createSpy = vi
      .spyOn(api, 'createIngredient')
      .mockResolvedValue({ id: '1', name: 'Sugar', unit: 'kg', cost: 1 });

    render(
      <AuthProvider>
        <MemoryRouter>
          <Ingredients />
        </MemoryRouter>
      </AuthProvider>
    );

    fireEvent.change(screen.getByLabelText('name'), { target: { value: 'Sugar' } });
    fireEvent.change(screen.getByLabelText('unit'), { target: { value: 'kg' } });
    fireEvent.change(screen.getByLabelText('cost'), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: /add/i }));

    expect(createSpy).toHaveBeenCalledWith({ name: 'Sugar', unit: 'kg', cost: 1 });

    createSpy.mockRestore();
    listSpy.mockRestore();
  });
});
