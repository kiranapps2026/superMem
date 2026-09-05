'use client';

import { useCallback, useEffect, useState } from 'react';
import { SourceOut, SourceListResponse, FactItem, DecisionItem, IngestJobOut, IngestUploadResponse, PaginatedResponse } from '@/types/api';
import { apiGet, apiPost, apiDelete, uploadFile } from '@/lib/api';

export function useSources(projectId: string) {
  const [items, setItems] = useState<SourceOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<SourceListResponse>(`/api/v1/ingest/sources?project_id=${encodeURIComponent(projectId)}`);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sources');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  return { items, total, loading, error, reload: load };
}

export function useFacts(projectId: string) {
  const [items, setItems] = useState<FactItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<PaginatedResponse<FactItem>>(`/api/v1/ingest/facts?project_id=${encodeURIComponent(projectId)}`);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load facts');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  return { items, total, loading, error, reload: load };
}

export function useDecisions(projectId: string) {
  const [items, setItems] = useState<DecisionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<PaginatedResponse<DecisionItem>>(`/api/v1/ingest/decisions?project_id=${encodeURIComponent(projectId)}`);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load decisions');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  return { items, total, loading, error, reload: load };
}

// Partial shape returned by uploadFile() before the full pipeline completes
interface PartialUploadResponse {
  source_id: string;
  status: string;
}

export function useUploadFile(projectId: string) {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PartialUploadResponse | null>(null);

  const upload = useCallback(async (file: File, onProgress?: (p: number) => void): Promise<PartialUploadResponse | null> => {
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(0);
    try {
      const res = await uploadFile(projectId, file, onProgress ?? setProgress);
      setResult(res);
      return res;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const reset = useCallback(() => { setResult(null); setError(null); setProgress(0); }, []);

  return { upload, loading, progress, error, result, reset };
}

export function useIngestJobs() {
  const [jobs, setJobs] = useState<IngestJobOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<IngestJobOut[]>('/api/v1/ingest/jobs');
      setJobs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return { jobs, loading, error, reload: load };
}
