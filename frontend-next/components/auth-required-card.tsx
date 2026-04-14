import Link from 'next/link';
import { buildLoginHref } from '@/lib/auth';

export function AuthRequiredCard({
  nextPath,
  title = 'Sign in required',
  detail,
}: {
  nextPath: string;
  title?: string;
  detail: string;
}) {
  return (
    <section className="card stack" style={{ maxWidth: 720 }}>
      <div className="label">Authenticated preview</div>
      <h1 style={{ margin: 0 }}>{title}</h1>
      <p className="muted" style={{ margin: 0 }}>{detail}</p>
      <div className="row">
        <Link className="button primary" href={buildLoginHref(nextPath)}>
          Go to login
        </Link>
        <Link className="button" href="/">
          Back to landing
        </Link>
      </div>
    </section>
  );
}
