'use client';
import { useEffect, useState, useCallback } from 'react';
import { MemoryItemOut } from '@/types/api';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { Brain, Filter, X } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { Pagination } from '@/components/ui/Pagination';

const PAGE_SIZE = 20;

export default function MemoryPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [items, setItems] = useState<MemoryItemOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [memoryType, setMemoryType] = useState('');
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const url = `/api/v1/memory/?limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}&project_id=${encodeURIComponent(projectId)}${memoryType ? `&memory_type=${encodeURIComponent(memoryType)}` : ''}`;
      const data = await apiGet<MemoryItemOut[]>(url);
      setItems(data);
      setTotal(data.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load memory');
    } finally { setLoading(false); }
  }, [user, projectId, memoryType, page]);

  useEffect(() => { loadData(); }, [loadData]);

  const tagsFor = (item: MemoryItemOut): string[] => (item.extra_metadata?.tags as string[]) || [];
  // Backend stores lowercase temporal_status; Badge expects ACTIVE/SUPERSEDED/ARCHIVED
  const temporalLabel = (s: string) => ({ current: 'ACTIVE', superseded: 'SUPERSEDED', archived: 'ARCHIVED' }[s.toLowerCase()] ?? s.toUpperCase());

  if (!user) {
    return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to view memory.</p></div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Memory</h1>
          <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">{total} item{total !== 1 ? 's' : ''} in this project</p>
        </div>
        <div className="relative">
          <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--sv-text-disabled)]" />
          <select
            value={memoryType}
            onChange={(e) => { setMemoryType(e.target.value); setPage(0); }}
            className="bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md pl-8 pr-3 py-1.5 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors appearance-none"
          >
            <option value="">All types</option>
            <option value="semantic_memory">Semantic</option>
            <option value="episodic_memory">Episodic</option>
            <option value="procedural_memory">Procedural</option>
            <option value="working_memory">Working</option>
          </select>
        </div>
      </div>

      {/* Error */}
      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* Loading */}
      {loading && <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>}

      {/* Empty */}
      {!loading && items.length === 0 && !error && (
        <EmptyState
          icon={<Brain size={32} className="text-[var(--sv-text-disabled)]" />}
          title="No memory yet"
          description="Ingest sessions or chat with AI to build project memory."
        />
      )}

      {/* List */}
      <div className="space-y-2">
        {items.map((item) => (
          <div key={item.id} className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-4 hover:border-[var(--sv-accent)]/30 transition-colors">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <Badge variant="muted" size="sm">{item.memory_type.replace('_memory', '')}</Badge>
                <span className="text-xs text-[var(--sv-text-disabled)]">Authority: {Math.round(item.authority * 100)}%</span>
                {item.temporal_status && <Badge category="temporal" value={temporalLabel(item.temporal_status)} size="sm" />}
              </div>
              <span className="text-xs text-[var(--sv-text-disabled)]">{new Date(item.created_at).toLocaleString()}</span>
            </div>
            <p className="text-sm text-[var(--sv-text-secondary)] leading-relaxed line-clamp-3">{item.content}</p>
            <div className="flex items-center justify-between mt-2">
              <div className="flex flex-wrap gap-1">
                {tagsFor(item).map((t: string) => (
                  <span key={t} className="text-[10px] text-[var(--sv-text-tertiary)] bg-[var(--sv-bg-overlay)] px-1.5 py-0.5 rounded border border-[var(--sv-border-subtle)]">{t}</span>
                ))}
              </div>
              <span className="text-[10px] text-[var(--sv-text-disabled)]">Confidence: {Math.round(item.confidence * 100)}%</span>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {items.length >= PAGE_SIZE && (
        <div className="pt-2">
          <Pagination page={page} totalPages={page + 2} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
