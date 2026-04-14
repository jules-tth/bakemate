'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { loginWithPassword, writeStoredToken } from '@/lib/auth';

export function LoginForm({ nextPath }: { nextPath: string }) {
  const router = useRouter();
  const [username, setUsername] = useState('admin@example.com');
  const [password, setPassword] = useState('password');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const result = await loginWithPassword(username, password);
      writeStoredToken(result.access_token);
      router.push(nextPath);
    } catch {
      setError('Login preview failed. Check API availability and credentials.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="shell">
      <div className="card stack" style={{ maxWidth: 480 }}>
        <div className="label">Preview login</div>
        <h1 style={{ margin: 0 }}>Sign in with the current token flow</h1>
        <p className="muted" style={{ margin: 0 }}>
          This preview uses the same form-encoded login request shape and the same localStorage token key as the current frontend,
          then hands off into the requested authenticated preview route.
        </p>
        <div className="card" style={{ padding: 14 }}>
          <div className="label">After sign-in</div>
          <div className="muted" style={{ marginTop: 8 }}>You will continue to <code>{nextPath}</code>.</div>
        </div>
        <form className="stack" onSubmit={handleSubmit}>
          <label className="stack" style={{ gap: 8 }}>
            <span className="label">Username</span>
            <input className="input" value={username} onChange={(event) => setUsername(event.target.value)} />
          </label>
          <label className="stack" style={{ gap: 8 }}>
            <span className="label">Password</span>
            <input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          <button className="button primary" disabled={isSubmitting} type="submit">
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        {error ? <div className="error">{error}</div> : null}
        <div className="row">
          <Link className="button" href="/">
            Back to landing
          </Link>
        </div>
      </div>
    </main>
  );
}
