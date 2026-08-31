'use client';
import { useEffect, useState, useCallback } from 'react';
import { apiGet, apiPost, getToken } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { Search as SearchIcon } from 'lucide-react';

interface SearchResult {
  item_type: string;
  id: string;
  score: number;
  content: string;
  temporal_status: string | null;
  created_at: string;
}

export default function SearchPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [total, setTotal] = useState(0);
  const [searched, setSearched] = useState(false);

  const doSearch = useCallback(async () => {
    if (!query.trim() || !user) return;
    setSearching(true);
    setSearched(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const token = getToken();
      const res = await fetch(
        `${API_BASE}/api/v1/ingest/search?query=${encodeURIComponent(query.trim())}&limit=20&project_id=${encodeURIComponent(projectId)}`,
        { headers: { 'Authorization': token ? `Bearer ${token}` : '' } }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json() as { items: SearchResult[]; total: number };
      setResults(data.items || []);
      setTotal(data.total || 0);
    } catch {}
    finally { setSearching(false); }
  }, [query, user, projectId]);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-4">Search</h1>
      <div className="flex gap-2 mb-6">
        <input value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') doSearch(); }}
          placeholder="Search memories, facts, decisions…" autoFocus
          className="flex-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]" />
        <button onClick={doSearch} disabled={searching || !query.trim()} className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 rounded-md disabled:opacity-50">
          <SearchIcon size={16} />
        </button>
      </div>
      {searching ? <div className="text-sm text-gray-500">Searching…</div> : searched && results.length === 0 ? (
        <p className="text-sm text-gray-500">No results found for &ldquo;{query}&rdquo;.</p>
      ) : (
        <div>
          {total > 0 && <p className="text-xs text-gray-500 mb-3">{total} results</p>}
          <div className="space-y-2">
            {results.map((r) => (
              <div key={r.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium bg-[var(--bg-tertiary)] px-2 py-0.5 rounded text-gray-400">{r.item_type}</span>
                  <span className="text-xs text-gray-500">{new Date(r.created_at).toLocaleString()}</span>
                </div>
                <p className="text-sm text-gray-300 line-clamp-3">{r.content}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs text-gray-500">Score: {Math.round(r.score * 100)}%</span>
                  {r.temporal_status && <span className="text-xs text-gray-500">{r.temporal_status}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
