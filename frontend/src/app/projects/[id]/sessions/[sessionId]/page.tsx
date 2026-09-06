'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { User, Bot, ArrowLeft } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';

interface SessionHistory {
  session_id: string;
  title: string | null;
  source: string;
  messages: { id: string; role: string; content: string; created_at: string | null }[];
}

export default function SessionDetailPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const sessionId = params.sessionId as string;
  const [history, setHistory] = useState<SessionHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    apiGet<SessionHistory>(`/api/v1/sessions/${sessionId}/history`)
      .then(setHistory)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load session'))
      .finally(() => setLoading(false));
  }, [user, sessionId]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div></div>;
  if (!history) return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Session not found.</p></div>;

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4">
      {/* Header */}
      <div>
        <Link href={`/projects/${projectId}/sessions`} className="inline-flex items-center gap-1 text-xs text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] transition-colors">
          <ArrowLeft size={14} /> All Sessions
        </Link>
        <div className="mt-3 flex items-center gap-2">
          <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">{history.title || 'Untitled session'}</h1>
          <Badge variant="muted" size="sm">{history.source}</Badge>
        </div>
        <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">{history.messages.length} messages</p>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* Messages */}
      <div className="space-y-3">
        {history.messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-[var(--sv-accent)]' : 'bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)]'}`}>
              {msg.role === 'user' ? <User size={14} className="text-white" /> : <Bot size={14} className="text-[var(--sv-text-tertiary)]" />}
            </div>
            <div className={`max-w-[75%] px-3.5 py-2.5 rounded-xl text-sm whitespace-pre-wrap leading-relaxed ${msg.role === 'user' ? 'bg-[var(--sv-accent)] text-[var(--sv-text-inverse)] rounded-tr-sm' : 'bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-tl-sm text-[var(--sv-text-primary)]'}`}>
              {msg.content}
              {msg.created_at && <p className="text-[10px] text-[var(--sv-text-disabled)] mt-1">{new Date(msg.created_at).toLocaleString()}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
