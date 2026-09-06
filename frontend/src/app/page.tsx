'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { Brain } from 'lucide-react';

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading) router.replace(user ? '/dashboard' : '/auth/login');
  }, [user, loading, router]);
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--sv-bg-primary)]">
      <div className="text-center">
        <Brain size={48} className="mx-auto text-[var(--sv-accent)] mb-4" />
        <p className="text-sm text-[var(--sv-text-tertiary)]">Loading…</p>
      </div>
    </div>
  );
}
