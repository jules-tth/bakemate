import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import RecipeDetail from './RecipeDetail';
import * as api from '../api/recipes';

describe('RecipeDetail page', () => {
  it('updates a recipe', async () => {
    const getSpy = vi
      .spyOn(api, 'getRecipe')
      .mockResolvedValue({ id: '1', name: 'Cake', description: 'Yum' });
    const updateSpy = vi
      .spyOn(api, 'updateRecipe')
      .mockResolvedValue({ id: '1', name: 'Cake2', description: 'Yum2' });

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/recipes/1"]}>
          <Routes>
            <Route path="/recipes/:id" element={<RecipeDetail />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    await screen.findByDisplayValue('Cake');
    fireEvent.change(screen.getByLabelText('name'), { target: { value: 'Cake2' } });
    fireEvent.change(screen.getByLabelText('description'), {
      target: { value: 'Yum2' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    expect(updateSpy).toHaveBeenCalledWith('1', {
      name: 'Cake2',
      description: 'Yum2',
    });

    getSpy.mockRestore();
    updateSpy.mockRestore();
  });
});
