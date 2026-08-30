'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { SessionHistory } from '@/types/api';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { User, Bot } from 'lucide-react';

export default function SessionDetailPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const sessionId = params.sessionId as string;
  const [history, setHistory] = useState<SessionHistory | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    apiGet<SessionHistory>(`/api/v1/projects/${projectId}/sessions/${sessionId}`).then((h) => { setHistory(h); setLoading(false); }).catch(() => setLoading(false));
  }, [user, projectId, sessionId]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;
  if (!history) return <div className="flex items-center justify-center h-full"><p className="text-gray-500 text-sm">Session not found.</p></div>;

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="mb-6">
        <Link href={`/projects/${projectId}/sessions`} className="text-xs text-gray-500 hover:text-white">&larr; All Sessions</Link>
        <h1 className="text-xl font-semibold mt-2">{history.title || 'Untitled session'}</h1>
        <p className="text-sm text-gray-500">{history.source} &middot; {history.messages.length} messages</p>
      </div>
      <div className="space-y-3">
        {history.messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-[var(--accent)]' : 'bg-[var(--bg-tertiary)]'}`}>
              {msg.role === 'user' ? <User size={14} className="text-white" /> : <Bot size={14} className="text-gray-400" />}
            </div>
            <div className={`max-w-[75%] px-3 py-2 rounded-lg text-sm whitespace-pre-wrap ${msg.role === 'user' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-secondary)] border border-[var(--border)]'}`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}