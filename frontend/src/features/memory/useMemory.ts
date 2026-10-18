'use client';

import { useCallback, useEffect, useState } from 'react';
import { MemoryItemOut, MemorySearchRequest } from '@/types/api';
import { apiGet, apiPost, apiDelete } from '@/lib/api';

interface UseMemoryListOptions {
  projectId: string;
  memoryType?: string;
  limit?: number;
}

export function useMemoryList({ projectId, memoryType, limit = 50 }: UseMemoryListOptions) {
  const [items, setItems] = useState<MemoryItemOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (offset = 0) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
        project_id: projectId,
      });
      if (memoryType) params.set('memory_type', memoryType);
      const data = await apiGet<MemoryItemOut[]>(`/api/v1/memory/?${params}`);
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load memory');
    } finally {
      setLoading(false);
    }
  }, [projectId, memoryType, limit]);

  useEffect(() => { load(); }, [load]);

  return { items, loading, error, reload: load };
}

export function useMemorySearch(query: string, options?: { projectId?: string; limit?: number }) {
  const [results, setResults] = useState<MemoryItemOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async () => {
    if (!query.trim()) { setResults([]); return; }
    setLoading(true);
    setError(null);
    try {
      const body: MemorySearchRequest = { query: query.trim(), limit: options?.limit ?? 20, project_id: options?.projectId ?? null };
      const data = await apiPost<MemoryItemOut[]>('/api/v1/memory/search', body);
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

export function useCreateMemory() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(async (data: {
    project_id: string;
    memory_type: string;
    content: string;
    confidence?: number;
    extra_metadata?: Record<string, unknown>;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiPost<MemoryItemOut>('/api/v1/memory/', data);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create memory');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { create, loading, error };
}

export function useDeleteMemory() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const remove = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await apiDelete(`/api/v1/memory/${id}`);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete memory');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return { remove, loading, error };
}
