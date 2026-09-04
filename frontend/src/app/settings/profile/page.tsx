'use client';
import { useState, FormEvent, useEffect } from 'react';
import {
  Card, Badge, EmptyState, LoadingSpinner, ConfirmDialog
} from '@/components/ui';
import { User, Shield, Lock, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { apiPost, apiPatch } from '@/lib/api';

export default function ProfilePage() {
  const { user, loading: authLoading } = useAuth();
  const [saving, setSaving] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [name, setName] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    if (user?.name) setName(user.name);
  }, [user]);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const saveProfile = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiPatch('/api/v1/auth/me', { name });
      showMessage('success', 'Profile updated');
    } catch {
      showMessage('error', 'Failed to update profile');
    } finally { setSaving(false); }
  };

  const changePassword = async (e: FormEvent) => {
    e.preventDefault();
    setChangingPassword(true);
    try {
      await apiPost('/api/v1/auth/change-password', { current_password: currentPassword, new_password: newPassword });
      showMessage('success', 'Password updated');
      setCurrentPassword('');
      setNewPassword('');
    } catch {
      showMessage('error', 'Failed to change password');
    } finally { setChangingPassword(false); }
  };

  if (authLoading) {
    return <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>;
  }

  if (!user) {
    return <div className="p-6 text-sm text-gray-500">Not authenticated.</div>;
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="flex items-center gap-2 mb-1">
        <User size={18} className="text-gray-500" />
        <h1 className="text-xl font-semibold">Profile</h1>
      </div>
      <p className="text-sm text-gray-500 mb-6">Manage your account details and security.</p>

      {message && (
        <div className={`mb-4 px-4 py-2.5 rounded-lg text-sm ${message.type === 'error' ? 'bg-red-500/10 border border-red-500/30 text-red-400' : 'bg-green-500/10 border border-green-500/30 text-green-400'}`}>
          {message.text}
        </div>
      )}

      <div className="space-y-6">
        <Card title="Account Information" subtitle="Your public profile details">
          <form onSubmit={saveProfile} className="space-y-4">
            <div>
              <label htmlFor="profile-name" className="block text-xs text-gray-500 mb-1">Name</label>
              <input
                id="profile-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Email</label>
              <p className="text-sm text-gray-300 bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2">{user.email}</p>
            </div>
            <button type="submit" disabled={saving} className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-1.5 rounded-md text-sm disabled:opacity-50 transition-colors">
              {saving ? 'Saving…' : 'Save Profile'}
            </button>
          </form>
        </Card>

        <Card title="Security" subtitle="Change your password">
          <form onSubmit={changePassword} className="space-y-4">
            <div>
              <label htmlFor="current-password" className="block text-xs text-gray-500 mb-1">Current Password</label>
              <input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
            <div>
              <label htmlFor="new-password" className="block text-xs text-gray-500 mb-1">New Password</label>
              <div className="relative">
                <input
                  id="new-password"
                  type={showPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                  className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 pr-10 text-sm focus:outline-none focus:border-[var(--accent)]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={changingPassword} className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-1.5 rounded-md text-sm disabled:opacity-50 transition-colors flex items-center gap-1.5">
              <Lock size={14} />{changingPassword ? 'Updating…' : 'Update Password'}
            </button>
          </form>
        </Card>
      </div>
    </div>
  );
}
