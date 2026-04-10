'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { loginWithPassword, writeStoredToken } from '@/lib/auth';

export default function LoginPage() {
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
      router.push('/ops');
    } catch {
      setError('Login proof failed. Check API availability and credentials.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="shell">
      <div className="card stack" style={{ maxWidth: 480 }}>
        <div className="label">Auth compatibility proof</div>
        <h1 style={{ margin: 0 }}>Sign in with the current token flow</h1>
        <p className="muted" style={{ margin: 0 }}>
          This scaffold uses the same form-encoded login request shape and the same localStorage token key as the current frontend.
        </p>
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
      </div>
    </main>
  );
}
