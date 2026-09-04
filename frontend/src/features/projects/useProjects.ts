'use client';

import { useCallback, useEffect, useState } from 'react';
import { Project, ProjectCreate, ProjectUpdate } from '@/types/api';
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api';

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<Project[]>('/api/v1/projects/');
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return { projects, loading, error, reload: load };
}

export function useProject(id: string | null) {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!id) { setLoading(false); return; }
    setLoading(true);
    setError(null);
    try {
      const p = await apiGet<Project>(`/api/v1/projects/${id}`);
      setProject(p);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Not found');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { reload(); }, [reload]);

  return { project, loading, error, reload };
}

export function useCreateProject() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(async (data: ProjectCreate): Promise<Project | null> => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiPost<Project>('/api/v1/projects/', data);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { create, loading, error };
}

export function useUpdateProject(id: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = useCallback(async (data: ProjectUpdate): Promise<Project | null> => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiPatch<Project>(`/api/v1/projects/${id}`, data);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update project');
      return null;
    } finally {
      setLoading(false);
    }
  }, [id]);

  return { update, loading, error };
}

export function useDeleteProject() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const remove = useCallback(async (id: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      await apiDelete(`/api/v1/projects/${id}`);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete project');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return { remove, loading, error };
}
