'use client';

import { useCallback, useEffect, useState } from 'react';
import { GraphResponse } from '@/types/api';
import { apiGet } from '@/lib/api';

export function useGraph(projectId: string) {
  const [data, setData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiGet<GraphResponse>(`/api/v1/graph?project_id=${encodeURIComponent(projectId)}`);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load graph');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  return { data, loading, error, reload: load };
}
