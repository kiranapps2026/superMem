'use client';
import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { UserPlus, Lock } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [name, setName] = useState('');
  const [workspaceName, setWorkspaceName] = useState('');
  const { register, loading, error, clearError } = useAuth();
  const router = useRouter();
  const passwordMismatch = password !== confirm && confirm.length > 0;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await register({ email, password, name: name || '', workspace_name: workspaceName });
      router.push('/dashboard');
    } catch {}
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--sv-bg-primary)]">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-[var(--sv-text-primary)]">Create your account</h1>
          <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">Get started with SwarmVault</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <ErrorAlert message={error} onDismiss={clearError} />}
          {passwordMismatch && (
            <ErrorAlert message="Passwords do not match" onDismiss={() => {}} />
          )}
          <div>
            <label className="block text-sm text-[var(--sv-text-tertiary)] mb-1">Full name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} autoFocus
              className="w-full bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" placeholder="Jane Doe" />
          </div>
          <div>
            <label className="block text-sm text-[var(--sv-text-tertiary)] mb-1">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
              className="w-full bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" placeholder="you@example.com" />
          </div>
          <div>
            <label className="block text-sm text-[var(--sv-text-tertiary)] mb-1">Workspace name</label>
            <input type="text" value={workspaceName} onChange={(e) => setWorkspaceName(e.target.value)} required
              className="w-full bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" placeholder="Acme Corp" />
          </div>
          <div>
            <label className="block text-sm text-[var(--sv-text-tertiary)] mb-1">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8}
              className="w-full bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" placeholder="Min 8 characters" />
          </div>
          <div>
            <label className="block text-sm text-[var(--sv-text-tertiary)] mb-1">Confirm password</label>
            <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required
              className="w-full bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" placeholder="Repeat password" />
          </div>
          <button type="submit" disabled={loading || passwordMismatch}
            className="w-full bg-[var(--sv-accent)] hover:bg-[var(--sv-accent-hover)] text-[var(--sv-text-inverse)] py-2 rounded-md text-sm font-medium disabled:opacity-50 transition-colors">
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <p className="text-center text-sm text-[var(--sv-text-tertiary)] mt-6">
          Already have an account? <Link href="/auth/login" className="text-[var(--sv-accent)] hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
