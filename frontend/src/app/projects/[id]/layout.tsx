'use client';
import { useEffect, useState, FormEvent } from 'react';
import Link from 'next/link';
import { Project } from '@/types/api';
import { apiGet, apiPatch, apiDelete } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { Settings, Trash2, X, Check } from 'lucide-react';

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!projectId || !user) return;
    apiGet<Project>(`/api/v1/projects/${projectId}`).then((p) => {
      setProject(p); setEditName(p.name); setEditDesc(p.description || ''); setLoading(false);
    }).catch(() => setLoading(false));
  }, [projectId, user]);

  const saveProject = async (e: FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      const data: { name?: string; description?: string | null } = {};
      if (editName !== project?.name) data.name = editName;
      if (editDesc !== (project?.description || '')) data.description = editDesc;
      if (Object.keys(data).length) {
        const updated = await apiPatch<Project>(`/api/v1/projects/${projectId}`, data);
        setProject(updated);
      }
      setEditing(false);
    } catch { alert('Failed to save'); }
    finally { setSaving(false); }
  };

  const deleteProject = async () => {
    if (!confirm('Delete this project and all its data?')) return;
    try { await apiDelete(`/api/v1/projects/${projectId}`); window.location.href = '/projects'; }
    catch { alert('Failed to delete'); }
  };

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;
  if (!project) return <div className="flex items-center justify-center h-full"><p className="text-gray-500 text-sm">Project not found.</p></div>;

  return (
    <div className="flex h-full">
      <div className="w-48 shrink-0 border-r border-[var(--border)] p-3 flex flex-col gap-2">
        <Link href="/projects" className="text-xs text-gray-500 hover:text-white px-2 py-1">&larr; All Projects</Link>
        {!editing ? (
          <div>
            <h2 className="font-medium text-sm px-2 truncate">{project.name}</h2>
            {project.description && <p className="text-xs text-gray-500 px-2 line-clamp-2">{project.description}</p>}
            <div className="mt-2 space-y-0.5">
              <Link href={`/projects/${projectId}/chat`} className="block px-2 py-1 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded">Chat</Link>
              <Link href={`/projects/${projectId}/ingest`} className="block px-2 py-1 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded">Ingest</Link>
              <Link href={`/projects/${projectId}/sessions`} className="block px-2 py-1 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded">Sessions</Link>
              <Link href={`/projects/${projectId}/memory`} className="block px-2 py-1 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded">Memory</Link>
              <Link href={`/projects/${projectId}/facts`} className="block px-2 py-1 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded">Facts</Link>
              <Link href={`/projects/${projectId}/decisions`} className="block px-2 py-1 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded">Decisions</Link>
              <Link href={`/projects/${projectId}/timeline`} className="block px-2 py-1 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded">Timeline</Link>
              <Link href={`/projects/${projectId}/search`} className="block px-2 py-1 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded">Search</Link>
              <Link href={`/projects/${projectId}/graph`} className="block px-2 py-1 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded">Graph</Link>
            </div>
            <div className="mt-3 pt-3 border-t border-[var(--border)] space-y-0.5">
              <button onClick={() => setEditing(true)} className="w-full text-left flex items-center gap-2 px-2 py-1 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded"><Settings size={12} /> Settings</button>
              <button onClick={deleteProject} className="w-full text-left flex items-center gap-2 px-2 py-1 text-sm text-red-400 hover:bg-red-400/5 rounded"><Trash2 size={12} /> Delete</button>
            </div>
          </div>
        ) : (
          <form onSubmit={saveProject} className="space-y-2">
            <input value={editName} onChange={(e) => setEditName(e.target.value)} required className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded px-2 py-1 text-sm" />
            <textarea value={editDesc} onChange={(e) => setEditDesc(e.target.value)} rows={3} className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded px-2 py-1 text-sm" />
            <div className="flex gap-1">
              <button type="submit" disabled={saving} className="p-1 rounded bg-[var(--accent)] text-white"><Check size={12} /></button>
              <button type="button" onClick={() => setEditing(false)} className="p-1 rounded hover:bg-white/5"><X size={12} /></button>
            </div>
          </form>
        )}
      </div>
      <div className="flex-1 overflow-y-auto">{children}</div>
    </div>
  );
}