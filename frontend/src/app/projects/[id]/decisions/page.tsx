'use client';
import { useEffect, useState, useCallback } from 'react';
import { DecisionItem } from '@/types/api';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { CheckSquare, GitBranch } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { Pagination } from '@/components/ui/Pagination';

const PAGE_SIZE = 20;

export default function DecisionsPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [decisions, setDecisions] = useState<DecisionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<{ items: DecisionItem[] }>(`/api/v1/ingest/decisions?project_id=${encodeURIComponent(projectId)}&limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}`);
      setDecisions(data.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load decisions');
    } finally { setLoading(false); }
  }, [user, projectId, page]);

  useEffect(() => { loadData(); }, [loadData]);

  if (!user) {
    return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to view decisions.</p></div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Decisions</h1>
        <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">{decisions.length} decisions</p>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {loading && <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>}

      {!loading && decisions.length === 0 && !error && (
        <EmptyState
          icon={<CheckSquare size={32} className="text-[var(--sv-text-disabled)]" />}
          title="No decisions yet"
          description="Decisions are extracted from conversations where choices were made."
        />
      )}

      <div className="space-y-2">
        {decisions.map((d) => (
          <div key={d.id} className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-4 hover:border-[var(--sv-accent)]/30 transition-colors">
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm text-[var(--sv-text-primary)] leading-relaxed">{d.content}</p>
              <span className="text-xs text-[var(--sv-accent)] bg-[var(--sv-accent-subtle)] px-2 py-0.5 rounded-full font-medium shrink-0">{Math.round(d.confidence * 100)}%</span>
            </div>
            {d.context && <p className="text-xs text-[var(--sv-text-tertiary)] mt-1.5 italic">{d.context}</p>}
            <div className="flex items-center gap-2 mt-2">
              <Badge category="temporal" value={{ current: 'ACTIVE', superseded: 'SUPERSEDED', archived: 'ARCHIVED' }[d.temporal_status.toLowerCase()] ?? d.temporal_status.toUpperCase()} size="sm" />
              <Badge category="authority" value={d.authority >= 0.8 ? 'VERIFIED' : d.authority >= 0.5 ? 'OBSERVED' : 'INFERRED'} size="sm" />
              {d.superseded_by_id && <span className="text-xs text-[var(--sv-warning)]">Superseded</span>}
              <span className="text-xs text-[var(--sv-text-disabled)]">{new Date(d.created_at).toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>

      {decisions.length >= PAGE_SIZE && (
        <div className="pt-2">
          <Pagination page={page} totalPages={page + 2} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
