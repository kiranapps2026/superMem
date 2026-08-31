'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { MessageSquare, ChevronRight } from 'lucide-react';

interface SessionListItem {
  id: string;
  title: string | null;
  created_at: string | null;
  extra_metadata: Record<string, unknown> | null;
}

export default function SessionsPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    apiGet<SessionListItem[]>('/api/v1/sessions').then((s) => { setSessions(s); setLoading(false); }).catch(() => setLoading(false));
  }, [user]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  const metaFor = (s: SessionListItem) => s.extra_metadata || {};

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-1">Sessions</h1>
      <p className="text-sm text-gray-500 mb-4">All ingested conversations</p>
      {sessions.length === 0 ? <p className="text-sm text-gray-500">No sessions yet. Ingest conversations first.</p> : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <Link key={s.id} href={`/projects/${projectId}/sessions/${s.id}`} className="flex items-center justify-between bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-4 py-3 hover:border-[var(--accent)]/50 transition-colors">
              <div className="flex items-center gap-3">
                <MessageSquare size={16} className="text-gray-500" />
                <div>
                  <p className="text-sm font-medium">{s.title || 'Untitled session'}</p>
                  <p className="text-xs text-gray-500">{(metaFor(s) as any).source || 'chat'} &middot; {s.created_at ? new Date(s.created_at).toLocaleDateString() : ''}</p>
                </div>
              </div>
              <ChevronRight size={16} className="text-gray-500" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
