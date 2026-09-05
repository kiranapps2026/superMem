'use client';

import { useCallback, useEffect, useState } from 'react';
import { SearchResponse } from '@/types/api';
import { apiGet, apiPost } from '@/lib/api';

export function useSearch(query: string, options?: { projectId?: string; limit?: number }) {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async () => {
    if (!query.trim()) { setResults(null); return; }
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ query: query.trim(), limit: String(options?.limit ?? 20) });
      if (options?.projectId) params.set('project_id', options.projectId);
      const data = await apiPost<SearchResponse>(`/api/v1/ingest/search?${params}`, undefined);
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }, [query, options?.projectId, options?.limit]);

  useEffect(() => { search(); }, [search]);

  return { results, loading, error };
}
