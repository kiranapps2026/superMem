'use client';
import { useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter, usePathname } from 'next/navigation';

function AuthRedirect({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const publicPaths = ['/auth/login', '/auth/register'];
  const isPublic = publicPaths.includes(pathname);

  useEffect(() => {
    if (loading) return;
    if (!user && !isPublic) {
      router.replace('/auth/login');
    } else if (user && isPublic) {
      router.replace('/dashboard');
    }
  }, [user, loading, isPublic, router, pathname]);

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div></div>;
  }
  if (!user && !isPublic) return null;
  if (user && isPublic) return null;

  return <>{children}</>;
}

export { AuthRedirect };
