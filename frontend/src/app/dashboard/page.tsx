'use client';
import { useEffect, useState, FormEvent } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Project, WorkspaceDetail } from '@/types/api';
import { apiGet, apiPost } from '@/lib/api';
import { Plus, FolderOpen } from 'lucide-react';

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [workspace, setWorkspace] = useState<WorkspaceDetail | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!user) return;
    Promise.all([apiGet<WorkspaceDetail>('/api/v1/workspace'), apiGet<Project[]>('/api/v1/projects')])
      .then(([ws, proj]) => { setWorkspace(ws); setProjects(proj); })
      .finally(() => setLoading(false));
  }, [user]);

  const createProject = async (e: FormEvent) => {
    e.preventDefault(); setCreating(true);
    try {
      const project = await apiPost<Project>('/api/v1/projects', { name: newName, description: newDesc });
      setProjects((p) => [project, ...p]); setNewName(''); setNewDesc(''); setShowNew(false);
    } catch (err) { alert(err instanceof Error ? err.message : 'Failed'); }
    finally { setCreating(false); }
  };

  if (authLoading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;
  if (!user) return <div className="flex items-center justify-center h-full"><p className="text-gray-500 text-sm">Sign in to view dashboard.</p></div>;
  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold">{workspace?.name || 'Dashboard'}</h1>
          <p className="text-sm text-gray-500 mt-1">{projects.length} project{projects.length !== 1 ? 's' : ''}</p>
        </div>
        <button onClick={() => setShowNew(true)} className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-3 py-1.5 rounded-md text-sm font-medium">
          <Plus size={16} /> New Project
        </button>
      </div>
      {showNew && (
        <form onSubmit={createProject} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 mb-6 space-y-3">
          <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Project name" required
            className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]" />
          <input type="text" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} placeholder="Description (optional)"
            className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]" />
          <div className="flex gap-2">
            <button type="submit" disabled={creating} className="bg-[var(--accent)] text-white px-4 py-1.5 rounded-md text-sm disabled:opacity-50">
              {creating ? 'Creating…' : 'Create'}
            </button>
            <button type="button" onClick={() => setShowNew(false)} className="text-gray-400 hover:text-white px-4 py-1.5 rounded-md text-sm">Cancel</button>
          </div>
        </form>
      )}
      {projects.length === 0 ? (
        <div className="text-center py-20">
          <FolderOpen size={48} className="mx-auto text-gray-600 mb-4" />
          <p className="text-gray-500 text-sm">No projects yet.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`}
              className="block bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 hover:border-[var(--accent)]/50 transition-colors">
              <h3 className="font-medium text-sm">{p.name}</h3>
              {p.description && <p className="text-xs text-gray-500 mt-1 line-clamp-2">{p.description}</p>}
              <p className="text-xs text-gray-500 mt-3">{p.session_count} sessions</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
