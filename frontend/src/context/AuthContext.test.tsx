import React from 'react';
import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';

/**
 * Tests login and logout behavior for the Auth context.
 */

describe('AuthContext', () => {
  it('stores token on login and removes it on logout', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result } = renderHook(() => useAuth(), { wrapper });

    act(() => result.current.login('token123', 'refresh456'));
    expect(localStorage.getItem('token')).toBe('token123');
    expect(localStorage.getItem('refreshToken')).toBe('refresh456');
    expect(result.current.isAuthenticated).toBe(true);

    act(() => result.current.logout());
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('refreshToken')).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
