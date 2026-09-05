'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Project } from '@/types/api';
import { apiGet } from '@/lib/api';
import { FolderOpen, Search, Plus } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Tooltip } from '@/components/ui/Tooltip';
import { StatCard } from '@/components/ui/StatCard';

export default function ProjectsPage() {
  const { user, loading: authLoading } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!user) return;
    apiGet<Project[]>('/api/v1/projects').then((data) => { setProjects(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [user]);

  const filtered = projects.filter((p) =>
    !search || p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(search.toLowerCase()))
  );

  if (authLoading || loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Projects</h1>
          <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">{projects.length} total project{projects.length !== 1 ? 's' : ''}</p>
        </div>
        <Link href="/dashboard" className="flex items-center gap-2 text-sm text-[var(--sv-text-tertiary)] hover:text-[var(--sv-accent)] transition-colors">
          <Plus size={16} /> New Project
        </Link>
      </div>

      {projects.length > 5 && (
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--sv-text-tertiary)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search projects…"
            className="w-full bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg pl-9 pr-4 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-tertiary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors"
          />
        </div>
      )}

      {projects.length === 0 ? (
        <div className="text-center py-20 rounded-lg border border-[var(--sv-border-default)] bg-[var(--sv-bg-raised)]">
          <FolderOpen size={48} className="mx-auto text-[var(--sv-text-tertiary)] mb-4" />
          <p className="text-sm text-[var(--sv-text-tertiary)]">No projects yet. Create one from the Dashboard.</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 rounded-lg border border-[var(--sv-border-default)] bg-[var(--sv-bg-raised)]">
          <p className="text-sm text-[var(--sv-text-tertiary)]">No projects match &ldquo;{search}&rdquo;.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`}
              className="group block rounded-lg border border-[var(--sv-border-default)] bg-[var(--sv-bg-raised)] p-5 hover:border-[var(--sv-accent)]/50 hover:shadow-[0_0_0_1px_var(--sv-accent)] transition-all duration-[var(--sv-duration-fast)]">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-medium text-sm text-[var(--sv-text-primary)] group-hover:text-[var(--sv-accent)] transition-colors">{p.name}</h3>
                <Badge variant="muted" size="sm">Project</Badge>
              </div>
              {p.description && <p className="text-xs text-[var(--sv-text-tertiary)] line-clamp-2">{p.description}</p>}
              {!p.description && (
                <p className="text-xs text-[var(--sv-text-tertiary)] italic">No description</p>
              )}
              <div className="mt-4 flex items-center gap-3">
                <Tooltip text="Chat">
                  <Link href={`/projects/${p.id}/chat`} className="text-xs text-[var(--sv-text-tertiary)] hover:text-[var(--sv-accent)] transition-colors">Chat</Link>
                </Tooltip>
                <span className="text-[var(--sv-border-subtle)]">·</span>
                <Tooltip text="Ingest">
                  <Link href={`/projects/${p.id}/ingest`} className="text-xs text-[var(--sv-text-tertiary)] hover:text-[var(--sv-accent)] transition-colors">Ingest</Link>
                </Tooltip>
                <span className="text-[var(--sv-border-subtle)]">·</span>
                <Tooltip text="Memory">
                  <Link href={`/projects/${p.id}/memory`} className="text-xs text-[var(--sv-text-tertiary)] hover:text-[var(--sv-accent)] transition-colors">Memory</Link>
                </Tooltip>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
