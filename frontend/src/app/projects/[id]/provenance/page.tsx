'use client';
import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { apiGet } from '@/lib/api';
import { ProvenanceOut } from '@/types/api';
import { useParams } from 'next/navigation';
import { GitBranch, ChevronRight, MessageSquare, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorAlert } from '@/components/ui/ErrorAlert';

export default function ProvenancePage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [records, setRecords] = useState<ProvenanceOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<ProvenanceOut[]>(`/api/v1/provenance/?project_id=${encodeURIComponent(projectId)}`);
      setRecords(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load provenance');
    } finally { setLoading(false); }
  }, [user, projectId]);

  useEffect(() => { loadData(); }, [loadData]);

  if (!user) {
    return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to view provenance.</p></div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Provenance</h1>
        <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">{records.length} traced responses</p>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {loading && <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>}

      {!loading && records.length === 0 && !error && (
        <EmptyState
          icon={<GitBranch size={32} className="text-[var(--sv-text-disabled)]" />}
          title="No provenance records yet"
          description="Chat in the project to generate response traces."
        />
      )}

      <div className="space-y-2">
        {records.map((r) => {
          return (
            <div key={r.id} className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-4 hover:border-[var(--sv-accent)]/30 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <MessageSquare size={14} className="text-[var(--sv-text-tertiary)]" />
                  <span className="text-sm font-medium text-[var(--sv-text-primary)]">{r.model}</span>
                  <Badge variant="muted" size="sm">via {r.provider}</Badge>
                </div>
                <span className="text-xs text-[var(--sv-text-disabled)]">{new Date(r.created_at).toLocaleString()}</span>
              </div>

              <div className="flex flex-wrap gap-3 text-xs text-[var(--sv-text-tertiary)] mb-2">
                <span className="flex items-center gap-1"><Clock size={12} />{r.latency_ms}ms</span>
                <span>Tokens: {r.total_tokens}</span>
                <span>Method: {r.retrieval_method}</span>
                {r.confidence != null && <span title="Confidence score from retrieval (0-1)">Confidence: {(r.confidence * 100).toFixed(0)}%</span>}
              </div>

              {r.memory_ids_used && r.memory_ids_used.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 mt-2">
                  <span className="text-xs text-[var(--sv-text-tertiary)]">Sources:</span>
                  {r.memory_ids_used.slice(0, 5).map((mid, i) => (
                    <span key={i} className="text-xs bg-[var(--sv-bg-overlay)] border border-[var(--sv-border-subtle)] px-1.5 py-0.5 rounded font-mono text-[var(--sv-text-secondary)]">{mid.slice(0, 8)}</span>
                  ))}
                  {r.memory_ids_used.length > 5 && <span className="text-xs text-[var(--sv-text-tertiary)]">+{r.memory_ids_used.length - 5} more</span>}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
