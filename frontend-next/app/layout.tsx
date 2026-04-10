import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'BakeMate Next Scaffold',
  description: 'Parallel Next.js scaffold proof for BakeMate auth and /ops shell.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
