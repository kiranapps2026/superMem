'use client';
import { useEffect, useState, useCallback } from 'react';
import { FactItem } from '@/types/api';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { GitBranch, Plus } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { Pagination } from '@/components/ui/Pagination';

const PAGE_SIZE = 20;

export default function FactsPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [facts, setFacts] = useState<FactItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<{ items: FactItem[] }>(`/api/v1/ingest/facts?project_id=${encodeURIComponent(projectId)}&limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}`);
      setFacts(data.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load facts');
    } finally { setLoading(false); }
  }, [user, projectId, page]);

  useEffect(() => { loadData(); }, [loadData]);

  if (!user) {
    return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to view facts.</p></div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Facts</h1>
        <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">{facts.length} extracted facts</p>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {loading && <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>}

      {!loading && facts.length === 0 && !error && (
        <EmptyState
          icon={<GitBranch size={32} className="text-[var(--sv-text-disabled)]" />}
          title="No facts yet"
          description="Facts are extracted automatically when you ingest conversations or chat sessions."
        />
      )}

      <div className="space-y-2">
        {facts.map((f) => (
          <div key={f.id} className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-4 hover:border-[var(--sv-accent)]/30 transition-colors">
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm text-[var(--sv-text-primary)] leading-relaxed">{f.content}</p>
              <span className="text-xs text-[var(--sv-text-tertiary)] shrink-0">{Math.round(f.confidence * 100)}%</span>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Badge category="evidence" value={f.source_id ? 'PROVEN' : 'INGESTED'} size="sm" />
              {f.temporal_status && <Badge category="temporal" value={{ current: 'ACTIVE', superseded: 'SUPERSEDED', archived: 'ARCHIVED' }[f.temporal_status.toLowerCase()] ?? f.temporal_status.toUpperCase()} size="sm" />}
              <span className="text-xs text-[var(--sv-text-disabled)]">{new Date(f.created_at).toLocaleString()}</span>
            </div>
            <p className="text-xs text-[var(--sv-text-tertiary)] mt-2 font-mono">{f.subject} → {f.predicate} → {f.object}</p>
          </div>
        ))}
      </div>

      {facts.length >= PAGE_SIZE && (
        <div className="pt-2">
          <Pagination page={page} totalPages={page + 2} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
