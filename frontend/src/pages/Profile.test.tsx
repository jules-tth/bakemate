import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Profile from './Profile';
import * as usersApi from '../api/users';

describe('Profile page', () => {
  it('renders current user email', async () => {
    const user: usersApi.User = {
      id: '1',
      email: 'tester@example.com',
      is_active: true,
      is_superuser: false,
    };
    vi.spyOn(usersApi, 'getCurrentUser').mockResolvedValue(user);

    render(<Profile />);

    expect(await screen.findByText(/tester@example.com/i)).toBeInTheDocument();
  });
});

