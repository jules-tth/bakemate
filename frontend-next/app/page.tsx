import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="shell">
      <div className="card stack" style={{ maxWidth: 720 }}>
        <div className="label">Parallel scaffold proof</div>
        <h1 style={{ margin: 0 }}>BakeMate Next.js scaffold</h1>
        <p className="muted" style={{ margin: 0 }}>
          This parallel app now proves current auth/token compatibility, an authenticated `/ops` front door, and a first real `/orders` queue parity entry.
          It still does not replace the current frontend or claim order-detail parity.
        </p>
        <div className="row">
          <Link className="button primary" href="/login">
            Go to login proof
          </Link>
          <Link className="button" href="/ops">
            Go to /ops
          </Link>
          <Link className="button" href="/orders">
            Go to /orders
          </Link>
        </div>
      </div>
    </main>
  );
}
