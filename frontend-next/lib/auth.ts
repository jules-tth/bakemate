export const AUTH_TOKEN_STORAGE_KEY = 'token';
export const AUTH_API_PATH = '/auth/login/access-token';

export function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_URL || '/api/v1';
}

export function buildLoginRequestBody(username: string, password: string) {
  const params = new URLSearchParams();
  params.set('username', username);
  params.set('password', password);
  return params.toString();
}

export function buildLoginHref(nextPath = '/ops') {
  const params = new URLSearchParams();
  params.set('next', nextPath);
  return `/login?${params.toString()}`;
}

export function isMissingAuthTokenError(error: unknown) {
  return error instanceof Error && error.message === 'Missing auth token';
}

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export async function loginWithPassword(username: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${getApiBaseUrl()}${AUTH_API_PATH}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: buildLoginRequestBody(username, password),
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }

  return response.json();
}

export function readStoredToken() {
  if (typeof window === 'undefined') {
    return null;
  }

  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

export function writeStoredToken(token: string) {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}
