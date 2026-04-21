import test from 'node:test';
import assert from 'node:assert/strict';
import { AUTH_API_PATH, AUTH_TOKEN_STORAGE_KEY, buildLoginHref, buildLoginRequestBody, isMissingAuthTokenError } from '../lib/auth.ts';

test('next scaffold keeps the current auth token storage key', () => {
  assert.equal(AUTH_TOKEN_STORAGE_KEY, 'token');
});

test('next scaffold keeps the current auth token endpoint path', () => {
  assert.equal(AUTH_API_PATH, '/auth/login/access-token');
});

test('next scaffold uses form-encoded credentials', () => {
  assert.equal(buildLoginRequestBody('admin@example.com', 'password'), 'username=admin%40example.com&password=password');
});

test('next preview login can hand off into a requested authenticated route', () => {
  assert.equal(buildLoginHref('/orders/abc123'), '/login?next=%2Forders%2Fabc123');
});

test('next preview recognizes the current missing-token auth boundary', () => {
  assert.equal(isMissingAuthTokenError(new Error('Missing auth token')), true);
  assert.equal(isMissingAuthTokenError(new Error('Login failed')), false);
});
