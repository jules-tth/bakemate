import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { AuthProvider } from '../context/AuthContext';
import Reports from './Reports';

describe('Reports page', () => {
  it('shows links to report pages', () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <Reports />
        </MemoryRouter>
      </AuthProvider>
    );
    const links = screen.getAllByRole('link', { name: /view/i });
    expect(links).toHaveLength(3);
  });
});
