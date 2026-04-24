import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import Recipes from './Recipes';
import * as api from '../api/recipes';

describe('Recipes page', () => {
  it('creates recipe via form', async () => {
    const listSpy = vi.spyOn(api, 'listRecipes').mockResolvedValue([]);
    const createSpy = vi
      .spyOn(api, 'createRecipe')
      .mockResolvedValue({ id: '1', name: 'Cake', description: 'Yum' });

    render(
      <AuthProvider>
        <MemoryRouter>
          <Recipes />
        </MemoryRouter>
      </AuthProvider>
    );

    fireEvent.change(screen.getByLabelText('name'), { target: { value: 'Cake' } });
    fireEvent.change(screen.getByLabelText('description'), {
      target: { value: 'Yum' },
    });
    fireEvent.click(screen.getByRole('button', { name: /add recipe/i }));

    expect(createSpy).toHaveBeenCalledWith({ name: 'Cake', description: 'Yum' });

    createSpy.mockRestore();
    listSpy.mockRestore();
  });
});
