import Link from 'next/link';
import { buildLoginHref } from '@/lib/auth';

const previewSteps = [
  {
    label: '1. Land here',
    detail: 'Start from one honest public front door for BobbyD testing.',
  },
  {
    label: '2. Sign in',
    detail: 'Use the current BakeMate auth contract and token storage shape.',
  },
  {
    label: '3. Enter /ops',
    detail: 'Arrive in the accepted Next operator preview, then continue into queue and order detail.',
  },
];

export default function HomePage() {
  return (
    <main className="shell">
      <div className="stack" style={{ maxWidth: 880 }}>
        <section className="card stack">
          <div className="label">BM-093 live-testable preview front door</div>
          <h1 style={{ margin: 0 }}>BakeMate preview</h1>
          <p className="muted" style={{ margin: 0 }}>
            This Next app is now the first real BobbyD-testable front door for a bounded preview path: public landing, reachable login,
            authenticated `/ops`, queue handoff, and order-detail drill-in. React/Vite still remains the trusted live frontend.
          </p>
          <div className="row">
            <Link className="button primary" href={buildLoginHref('/ops')}>
              Sign in to preview
            </Link>
            <Link className="button" href="/ops">
              Open /ops preview
            </Link>
            <Link className="button" href="/orders">
              Open queue preview
            </Link>
          </div>
        </section>

        <section className="grid cols-3">
          {previewSteps.map((step) => (
            <article className="card" key={step.label}>
              <div className="label">{step.label}</div>
              <div className="muted" style={{ marginTop: 10 }}>{step.detail}</div>
            </article>
          ))}
        </section>

        <section className="card stack">
          <div className="label">Honest scope</div>
          <p className="muted" style={{ margin: 0 }}>
            This is a real testable preview front door, not a full frontend cutover claim. The accepted Next operator path is `/ops` → `/orders` → order detail,
            and anything beyond that still truthfully hands off to the current app.
          </p>
        </section>
      </div>
    </main>
  );
}
