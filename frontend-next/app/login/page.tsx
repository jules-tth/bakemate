import { LoginForm } from '@/components/login-form';

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const resolved = await searchParams;
  const nextPath = resolved.next && resolved.next.startsWith('/') ? resolved.next : '/ops';

  return <LoginForm nextPath={nextPath} />;
}
