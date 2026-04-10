import test from 'node:test';
import assert from 'node:assert/strict';
import { AUTH_API_PATH, AUTH_TOKEN_STORAGE_KEY, buildLoginRequestBody } from '../lib/auth.ts';

test('next scaffold keeps the current auth token storage key', () => {
  assert.equal(AUTH_TOKEN_STORAGE_KEY, 'token');
});

test('next scaffold keeps the current auth login path', () => {
  assert.equal(AUTH_API_PATH, '/auth/login');
});

test('next scaffold uses form-encoded credentials', () => {
  assert.equal(buildLoginRequestBody('admin@example.com', 'password'), 'username=admin%40example.com&password=password');
});
