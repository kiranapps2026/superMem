'use client';
import { useAuth } from '@/hooks/useAuth';
import { Sidebar } from '@/components/Sidebar';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const publicPaths = ['/auth/login', '/auth/register', '/'];
  const isAuthPage = pathname.startsWith('/auth/');

  useEffect(() => {
    if (loading) return;
    if (!user && !isAuthPage) {
      router.replace('/auth/login');
    } else if (user && isAuthPage) {
      router.replace('/dashboard');
    }
  }, [user, loading, isAuthPage, router, pathname]);

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div></div>;
  }

  // Auth pages - no sidebar
  if (isAuthPage) {
    return <>{children}</>;
  }

  // Not authenticated and not auth page - show nothing while redirecting
  if (!user) {
    return null;
  }

  // Authenticated - show sidebar + content
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
