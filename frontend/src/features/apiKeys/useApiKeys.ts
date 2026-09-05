'use client';

import { useCallback, useEffect, useState } from 'react';
import { apiGet, apiPost, apiDelete, apiPatch } from '@/lib/api';

export interface ApiKeyOut {
  id: string;
  key_prefix: string;
  name: string;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
  raw_key?: string;
}

export function useApiKeys() {
  const [keys, setKeys] = useState<ApiKeyOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<ApiKeyOut[]>('/api/v1/api-keys');
      setKeys(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return { keys, loading, error, reload: load };
}

export function useCreateKey() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rawKey, setRawKey] = useState<string | null>(null);

  const create = useCallback(async (name: string): Promise<ApiKeyOut | null> => {
    setLoading(true);
    setError(null);
    setRawKey(null);
    try {
      const result = await apiPost<ApiKeyOut & { raw_key: string }>('/api/v1/api-keys', { name });
      setRawKey(result.raw_key);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create API key');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearRawKey = useCallback(() => setRawKey(null), []);

  return { create, loading, error, rawKey, clearRawKey };
}

export function useRevokeKey() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const revoke = useCallback(async (id: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      await apiDelete(`/api/v1/api-keys/${id}`);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke key');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return { revoke, loading, error };
}

export function useRotateKey() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rawKey, setRawKey] = useState<string | null>(null);

  const rotate = useCallback(async (id: string): Promise<ApiKeyOut | null> => {
    setLoading(true);
    setError(null);
    setRawKey(null);
    try {
      const result = await apiPost<ApiKeyOut & { raw_key: string }>(`/api/v1/api-keys/${id}/rotate`, {});
      setRawKey(result.raw_key);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rotate key');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearRawKey = useCallback(() => setRawKey(null), []);

  return { rotate, loading, error, rawKey, clearRawKey };
}
