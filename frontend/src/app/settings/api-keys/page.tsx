'use client';

import { useState, useEffect, useCallback } from 'react';
import { useApiKeys, useCreateKey, useRevokeKey, useRotateKey } from '@/features/apiKeys/useApiKeys';
import type { ApiKeyOut } from '@/features/apiKeys/useApiKeys';
import {
  Card, EmptyState, LoadingSpinner, ConfirmDialog, useClipboard
} from '@/components/ui';
import { Key, Plus, Trash2, RefreshCw, Copy, Check, Shield } from 'lucide-react';

function formatDate(date: string | null): string {
  if (!date) return 'Never';
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function maskKey(prefix: string): string {
  return prefix + '••••••••••••••••••••';
}

export default function ApiKeysPage() {
  const { keys, loading, error, reload } = useApiKeys();
  const { create, loading: creating, rawKey, clearRawKey } = useCreateKey();
  const { revoke, loading: revoking } = useRevokeKey();
  const { rotate, loading: rotating, rawKey: rotatedKey, clearRawKey: clearRotatedKey } = useRotateKey();

  const [name, setName] = useState('');
  const [showRevoke, setShowRevoke] = useState<string | null>(null);
  const [showRotate, setShowRotate] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const { copied, copy } = useClipboard({ timeout: 3000 });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    const result = await create(name.trim());
    if (result) { setName(''); reload(); }
  };

  const handleRevoke = async () => {
    if (!showRevoke) return;
    await revoke(showRevoke);
    setShowRevoke(null);
    reload();
  };

  const handleRotate = async () => {
    if (!showRotate) return;
    const result = await rotate(showRotate);
    if (result) { setShowRotate(null); reload(); }
  };

  // Clear raw keys after interaction
  useEffect(() => {
    clearRawKey();
    clearRotatedKey();
  }, []);

  const RawKeyDisplay = ({ keyValue, label }: { keyValue: string; label: string }) => (
    <div className="bg-[var(--bg-primary)] border border-[var(--accent)]/30 rounded-lg p-4 mt-4">
      <p className="text-xs text-yellow-400 font-medium mb-2">{label} — copy this now. It won&apos;t be shown again.</p>
      <div className="flex items-center gap-2">
        <code className="flex-1 text-xs text-gray-300 break-all font-mono bg-black/30 rounded px-2 py-1">{keyValue}</code>
        <button onClick={() => copy(keyValue)} className="shrink-0 p-1.5 rounded hover:bg-white/5" aria-label="Copy key">
          {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} className="text-gray-400" />}
        </button>
      </div>
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="flex items-center gap-2 mb-1">
        <Shield size={18} className="text-gray-500" />
        <h1 className="text-xl font-semibold">API Keys</h1>
      </div>
      <p className="text-sm text-gray-500 mb-6">Manage workspace API keys for programmatic access.</p>

      {(error || localError) && (
        <div className="mb-4">
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-2.5 text-sm text-red-400">
            {localError || error}
          </div>
        </div>
      )}

      {rawKey && <RawKeyDisplay keyValue={rawKey} label="New API key created" />}
      {rotatedKey && <RawKeyDisplay keyValue={rotatedKey} label="API key rotated" />}

      <Card title="Create API Key" className="mb-6">
        <form onSubmit={handleCreate} className="flex gap-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Key name (e.g. CI/CD pipeline)"
            className="flex-1 bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
            required
          />
          <button type="submit" disabled={creating} className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-2 rounded-md text-sm disabled:opacity-50 whitespace-nowrap flex items-center gap-1.5">
            <Plus size={14} />{creating ? 'Creating…' : 'Create'}
          </button>
        </form>
      </Card>

      <Card title="Active Keys">
        {loading ? (
          <div className="flex justify-center py-8"><LoadingSpinner size="lg" /></div>
        ) : keys.length === 0 ? (
          <EmptyState icon={<Key size={24} />} title="No API keys" description="Create a key to enable programmatic access." />
        ) : (
          <div className="divide-y divide-[var(--border)]">
            {keys.map((k) => (
              <div key={k.id} className="flex items-center gap-4 px-4 py-3">
                <Key size={16} className="text-gray-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{k.name}</p>
                  <p className="text-xs text-gray-500 font-mono">{maskKey(k.prefix)} · Created {formatDate(k.created_at)} · Last used {formatDate(k.last_used_at)}</p>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => setShowRotate(k.id)}
                    className="p-1.5 rounded hover:bg-white/5 text-gray-400 hover:text-yellow-400"
                    aria-label={`Rotate key ${k.name}`}
                    title="Rotate key"
                  >
                    <RefreshCw size={14} />
                  </button>
                  <button
                    onClick={() => setShowRevoke(k.id)}
                    className="p-1.5 rounded hover:bg-white/5 text-gray-400 hover:text-red-400"
                    aria-label={`Revoke key ${k.name}`}
                    title="Revoke key"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <ConfirmDialog
        open={!!showRevoke}
        title="Revoke API key?"
        description="The key will be immediately invalidated. Any services using it will lose access."
        confirmLabel="Revoke"
        danger
        onConfirm={handleRevoke}
        onCancel={() => setShowRevoke(null)}
      />

      <ConfirmDialog
        open={!!showRotate}
        title="Rotate API key?"
        description="This creates a new key and invalidates the old one immediately. Update any services with the new key."
        confirmLabel="Rotate"
        danger
        onConfirm={handleRotate}
        onCancel={() => setShowRotate(null)}
      />
    </div>
  );
}
