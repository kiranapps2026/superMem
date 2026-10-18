'use client';
import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { Lock, UserPlus } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, loading, error, clearError } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    try { await login(email, password); router.push('/dashboard'); }
    catch {}
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--sv-bg-primary)]">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-[var(--sv-text-primary)]">Sign in to SwarmVault</h1>
          <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">Enter your credentials</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <ErrorAlert message={error} onDismiss={clearError} />}
          <div>
            <label className="block text-sm text-[var(--sv-text-tertiary)] mb-1">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus
              className="w-full bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" placeholder="you@example.com" />
          </div>
          <div>
            <label className="block text-sm text-[var(--sv-text-tertiary)] mb-1">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
              className="w-full bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" placeholder="Min 8 characters" />
          </div>
          <button type="submit" disabled={loading}
            className="w-full bg-[var(--sv-accent)] hover:bg-[var(--sv-accent-hover)] text-[var(--sv-text-inverse)] py-2 rounded-md text-sm font-medium disabled:opacity-50 transition-colors">
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="text-center text-sm text-[var(--sv-text-tertiary)] mt-6">
          Don&apos;t have an account? <Link href="/auth/register" className="text-[var(--sv-accent)] hover:underline">Create one</Link>
        </p>
      </div>
    </div>
  );
}
