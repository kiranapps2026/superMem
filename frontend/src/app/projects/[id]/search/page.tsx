'use client';
import { useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { apiPost, getToken } from '@/lib/api';
import { Search as SearchIcon, SlidersHorizontal, X } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { Pagination } from '@/components/ui/Pagination';
import type { SearchResultItem, SearchResponse } from '@/types/api';

const PAGE_SIZE = 10;

export default function SearchPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [total, setTotal] = useState(0);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [memoryType, setMemoryType] = useState<string>('');
  const inputRef = useRef<HTMLInputElement>(null);

  const doSearch = useCallback(async () => {
    if (!query.trim()) return;
    setSearching(true);
    setSearched(true);
    setError(null);
    setPage(1);
    try {
      const params = new URLSearchParams({ query: query.trim(), limit: String(PAGE_SIZE) });
      if (memoryType) params.set('memory_type', memoryType);
      const data = await apiPost<SearchResponse>(`/api/v1/ingest/search?${params.toString()}`, undefined);
      setResults(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally { setSearching(false); }
  }, [query, projectId, memoryType]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const paginatedResults = results.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (!user) {
    return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to search.</p></div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Search</h1>
        <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">Find memories, facts, and decisions across this project.</p>
      </div>

      {/* Search Input */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <SearchIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--sv-text-disabled)]" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { setPage(1); doSearch(); } }}
            placeholder="Search memories, facts, decisions…"
            autoFocus
            className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md pl-9 pr-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors"
          />
          {query && (
            <button onClick={() => { setQuery(''); setResults([]); setSearched(false); setError(null); }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--sv-text-disabled)] hover:text-[var(--sv-text-tertiary)] transition-colors">
              <X size={14} />
            </button>
          )}
        </div>
        <button onClick={() => { setPage(1); doSearch(); }} disabled={searching || !query.trim()}
          className="bg-[var(--sv-accent)] hover:bg-[var(--sv-accent-hover)] text-[var(--sv-text-inverse)] px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 transition-colors shrink-0">
          {searching ? 'Searching…' : 'Search'}
        </button>
        <div className="relative">
          <SlidersHorizontal size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--sv-text-disabled)]" />
          <select
            value={memoryType}
            onChange={(e) => { setMemoryType(e.target.value); setPage(1); }}
            className="bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md pl-9 pr-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors appearance-none"
          >
            <option value="">All types</option>
            <option value="semantic_memory">Semantic Memory</option>
            <option value="episodic_memory">Episodic Memory</option>
            <option value="procedural_memory">Procedural Memory</option>
            <option value="working_memory">Working Memory</option>
            <option value="fact">Facts</option>
            <option value="decision">Decisions</option>
          </select>
        </div>
      </div>

      {/* Error */}
      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* Results */}
      {searching && <div className="text-sm text-[var(--sv-text-tertiary)]">Searching…</div>}

      {searched && !searching && results.length === 0 && !error && (
        <EmptyState
          icon={<SearchIcon size={32} className="text-[var(--sv-text-disabled)]" />}
          title="No results found"
          description={`No knowledge items match "${query}". Try broader terms or different keywords.`}
        />
      )}

      {total > 0 && (
        <p className="text-xs text-[var(--sv-text-tertiary)]">
          {total} result{total !== 1 ? 's' : ''} {memoryType ? `in ${memoryType}` : 'across all types'}
        </p>
      )}

      <div className="space-y-2">
        {paginatedResults.map((r) => (
          <div key={r.id} className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-4 hover:border-[var(--sv-accent)]/30 transition-colors">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--sv-accent)] bg-[var(--sv-accent-subtle)] px-2 py-0.5 rounded-full font-medium">{r.item_type}</span>
                {r.temporal_status && <Badge category="temporal" value={{ current: 'ACTIVE', superseded: 'SUPERSEDED', archived: 'ARCHIVED' }[r.temporal_status.toLowerCase()] ?? r.temporal_status.toUpperCase()} size="sm" />}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--sv-text-tertiary)]">{Math.round(r.score * 100)}%</span>
                <span className="text-xs text-[var(--sv-text-disabled)]">{new Date(r.created_at).toLocaleString()}</span>
              </div>
            </div>
            <p className="text-sm text-[var(--sv-text-secondary)] leading-relaxed line-clamp-3">{r.content}</p>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pt-2">
          <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
