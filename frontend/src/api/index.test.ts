import { describe, expect, it, vi } from 'vitest';
import { AxiosError } from 'axios';
import apiClient, { handleApiError } from './index';

describe('handleApiError', () => {
  it('redirects to login on 401 without refresh token', async () => {
    const error = { response: { status: 401 } } as AxiosError;
    const redirect = vi.fn();
    await expect(handleApiError(error, redirect)).rejects.toBe(error);
    expect(redirect).toHaveBeenCalled();
  });

  it('refreshes token and retries request when refresh token exists', async () => {
    localStorage.setItem('refreshToken', 'r1');
    const error = { response: { status: 401 }, config: {} } as AxiosError;
    const refreshSpy = vi
      .spyOn(apiClient, 'post')
      .mockResolvedValue({ data: { access_token: 'a2', refresh_token: 'r2' } });
    const requestSpy = vi
      .spyOn(apiClient, 'request')
      .mockResolvedValue({ data: {} });

    await handleApiError(error, vi.fn());

    expect(refreshSpy).toHaveBeenCalledWith('/auth/refresh', {
      refresh_token: 'r1',
    });
    expect(requestSpy).toHaveBeenCalled();
    refreshSpy.mockRestore();
    requestSpy.mockRestore();
    localStorage.clear();
  });

  it('preserves existing Content-Type header', async () => {
    const params = new URLSearchParams();
    params.append('username', 'u');
    params.append('password', 'p');
    let capturedHeaders: Record<string, unknown> | undefined;
    await apiClient.post('/test', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      adapter: (config) => {
        capturedHeaders = config.headers;
        return Promise.resolve({
          data: {},
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
        });
      },
    });
    expect(capturedHeaders?.['Content-Type']).toBe(
      'application/x-www-form-urlencoded',
    );
  });
});
