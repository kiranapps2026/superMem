'use client';
import { useEffect, useState, useCallback } from 'react';
import { SearchResponse, SearchResult } from '@/types/api';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { Search, Shield } from 'lucide-react';

export default function SearchPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [count, setCount] = useState(0);

  const doSearch = useCallback(async () => {
    if (!query.trim() || !user) return;
    setSearching(true);
    try {
      const data = await apiGet<SearchResponse>(`/api/v1/memory/${projectId}/search?q=${encodeURIComponent(query.trim())}`);
      setResults(data.results); setCount(data.count);
    } catch {}
    finally { setSearching(false); }
  }, [query, user, projectId]);

  useEffect(() => { doSearch(); }, [doSearch]);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-4">Search</h1>
      <div className="flex gap-2 mb-6">
        <input value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') doSearch(); }}
          placeholder="Search memories, facts, decisions…" autoFocus
          className="flex-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]" />
        <button onClick={doSearch} disabled={searching} className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 rounded-md disabled:opacity-50">
          <Search size={16} />
        </button>
      </div>
      {searching ? <div className="text-sm text-gray-500">Searching…</div> : results.length === 0 ? (
        <p className="text-sm text-gray-500">{query ? 'No results found.' : 'Enter a query to search.'}</p>
      ) : (
        <div>
          <p className="text-xs text-gray-500 mb-3">{count} results</p>
          <div className="space-y-2">
            {results.map((r) => (
              <div key={r.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium bg-[var(--bg-tertiary)] px-2 py-0.5 rounded">{r.type}</span>
                    <span className="text-xs text-gray-500">{r.subtype}</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Shield size={12} />{Math.round(r.scores.final_score * 100)}%
                  </div>
                </div>
                <p className="text-sm text-gray-300 line-clamp-3">{r.content}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {r.tags.map((t) => <span key={t} className="text-xs text-gray-500 bg-[var(--bg-tertiary)] px-1.5 py-0.5 rounded">{t}</span>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}