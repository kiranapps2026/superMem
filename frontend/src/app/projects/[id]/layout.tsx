'use client';
import { useEffect, useState, FormEvent } from 'react';
import Link from 'next/link';
import { Project } from '@/types/api';
import { apiGet, apiPatch, apiDelete } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { Settings, Trash2, X, Check } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';

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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId || !user) return;
    apiGet<Project>(`/api/v1/projects/${projectId}`).then((p) => {
      setProject(p); setEditName(p.name); setEditDesc(p.description || ''); setLoading(false);
    }).catch(() => setLoading(false));
  }, [projectId, user]);

  const saveProject = async (e: FormEvent) => {
    e.preventDefault(); setSaving(true); setError(null);
    try {
      const data: { name?: string; description?: string | null } = {};
      if (editName !== project?.name) data.name = editName;
      if (editDesc !== (project?.description || '')) data.description = editDesc;
      if (Object.keys(data).length) {
        const updated = await apiPatch<Project>(`/api/v1/projects/${projectId}`, data);
        setProject(updated);
      }
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally { setSaving(false); }
  };

  const deleteProject = async () => {
    if (!confirm('Delete this project and all its data?')) return;
    try { await apiDelete(`/api/v1/projects/${projectId}`); window.location.href = '/projects'; }
    catch { alert('Failed to delete'); }
  };

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div></div>;
  if (!project) return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Project not found.</p></div>;

  const navItems = [
    { href: `/projects/${projectId}/chat`, label: 'Chat' },
    { href: `/projects/${projectId}/ingest`, label: 'Ingest' },
    { href: `/projects/${projectId}/sessions`, label: 'Sessions' },
    { href: `/projects/${projectId}/memory`, label: 'Memory' },
    { href: `/projects/${projectId}/facts`, label: 'Facts' },
    { href: `/projects/${projectId}/decisions`, label: 'Decisions' },
    { href: `/projects/${projectId}/timeline`, label: 'Timeline' },
    { href: `/projects/${projectId}/search`, label: 'Search' },
    { href: `/projects/${projectId}/graph`, label: 'Graph' },
  ];

  return (
    <div className="flex h-full">
      <div className="w-48 shrink-0 border-r border-[var(--sv-border-default)] p-3 flex flex-col gap-1">
        <Link href="/projects" className="text-xs text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] px-2 py-1.5 rounded-md transition-colors">&larr; All Projects</Link>

        {!editing ? (
          <>
            <div className="mt-2">
              <h2 className="font-medium text-sm text-[var(--sv-text-primary)] px-2 truncate">{project.name}</h2>
              {project.description && <p className="text-xs text-[var(--sv-text-tertiary)] px-2 line-clamp-2 mt-0.5">{project.description}</p>}
            </div>
            <nav className="mt-3 space-y-0.5">
              {navItems.map((item) => (
                <Link key={item.href} href={item.href} className="block px-2 py-1.5 text-sm text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] hover:bg-[var(--sv-bg-raised)] rounded-md transition-colors">
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="mt-auto pt-3 border-t border-[var(--sv-border-subtle)] space-y-0.5">
              <button onClick={() => setEditing(true)} className="w-full text-left flex items-center gap-2 px-2 py-1.5 text-sm text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] hover:bg-[var(--sv-bg-raised)] rounded-md transition-colors">
                <Settings size={12} /> Edit
              </button>
              <button onClick={deleteProject} className="w-full text-left flex items-center gap-2 px-2 py-1.5 text-sm text-[var(--sv-error)] hover:bg-[var(--sv-error)]/5 rounded-md transition-colors">
                <Trash2 size={12} /> Delete
              </button>
            </div>
          </>
        ) : (
          <form onSubmit={saveProject} className="mt-2 space-y-2">
            {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}
            <input value={editName} onChange={(e) => setEditName(e.target.value)} required
              className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-2 py-1.5 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" />
            <textarea value={editDesc} onChange={(e) => setEditDesc(e.target.value)} rows={3}
              className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-2 py-1.5 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors resize-none" />
            <div className="flex gap-1">
              <button type="submit" disabled={saving} className="p-1.5 rounded-md bg-[var(--sv-accent)] text-[var(--sv-text-inverse)] hover:bg-[var(--sv-accent-hover)] transition-colors disabled:opacity-50">
                <Check size={12} />
              </button>
              <button type="button" onClick={() => { setEditing(false); setError(null); }} className="p-1.5 rounded-md hover:bg-[var(--sv-bg-raised)] text-[var(--sv-text-tertiary)] transition-colors">
                <X size={12} />
              </button>
            </div>
          </form>
        )}
      </div>
      <div className="flex-1 overflow-y-auto">{children}</div>
    </div>
  );
}
