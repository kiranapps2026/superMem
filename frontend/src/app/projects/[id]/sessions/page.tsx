'use client';
import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { MessageSquare, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { Pagination } from '@/components/ui/Pagination';

const PAGE_SIZE = 20;

interface SessionListItem {
  id: string;
  title: string | null;
  created_at: string | null;
  updated_at: string | null;
  source: string | null;
  message_count: number | null;
}

export default function SessionsPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<SessionListItem[]>(`/api/v1/sessions/?project_id=${encodeURIComponent(projectId)}&limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}`);
      setSessions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions');
    } finally { setLoading(false); }
  }, [user, projectId, page]);

  useEffect(() => { loadData(); }, [loadData]);

  if (!user) {
    return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to view sessions.</p></div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Sessions</h1>
        <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">{sessions.length} sessions in this workspace</p>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {loading && <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>}

      {!loading && sessions.length === 0 && !error && (
        <EmptyState
          icon={<MessageSquare size={32} className="text-[var(--sv-text-disabled)]" />}
          title="No sessions yet"
          description="Sessions are created when you chat or ingest conversations."
        />
      )}

      <div className="space-y-2">
        {sessions.map((s) => (
          <Link key={s.id} href={`/projects/${projectId}/sessions/${s.id}`} className="flex items-center justify-between bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg px-4 py-3 hover:border-[var(--sv-accent)]/50 transition-colors">
            <div className="flex items-center gap-3">
              <MessageSquare size={16} className="text-[var(--sv-text-tertiary)]" />
              <div>
                <p className="text-sm font-medium text-[var(--sv-text-primary)]">{s.title || 'Untitled session'}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  {s.source && <Badge variant="muted" size="sm">{s.source}</Badge>}
                  {s.message_count !== null && <span className="text-xs text-[var(--sv-text-disabled)]">{s.message_count} messages</span>}
                  <span className="text-xs text-[var(--sv-text-disabled)]">{s.created_at ? new Date(s.created_at).toLocaleDateString() : ''}</span>
                </div>
              </div>
            </div>
            <ChevronRight size={16} className="text-[var(--sv-text-disabled)]" />
          </Link>
        ))}
      </div>

      {sessions.length >= PAGE_SIZE && (
        <div className="pt-2">
          <Pagination page={page} totalPages={page + 2} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
