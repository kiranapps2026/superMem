'use client';
import { useEffect, useState, FormEvent } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Project, WorkspaceDetail, DashboardSummary } from '@/types/api';
import { apiGet, apiPost } from '@/lib/api';
import {
  Plus, FolderOpen, Brain, Database, MessageSquare,
  ShieldCheck, Activity, Clock, GitBranch
} from 'lucide-react';
import { StatCard } from '@/components/ui/StatCard';
import { Badge } from '@/components/ui/Badge';
import { Tooltip } from '@/components/ui/Tooltip';

type View = 'overview' | 'recent';

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [workspace, setWorkspace] = useState<WorkspaceDetail | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [overview, setOverview] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [view, setView] = useState<View>('overview');
  const [wsCollapsed, setWsCollapsed] = useState(false);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      apiGet<WorkspaceDetail>('/api/v1/workspace'),
      apiGet<DashboardSummary>('/api/v1/dashboard/'),
      apiGet<Project[]>('/api/v1/projects'),
    ]).then(([ws, ov, proj]) => {
      setWorkspace(ws); setOverview(ov); setProjects(proj);
    }).finally(() => setLoading(false));
  }, [user]);

  const createProject = async (e: FormEvent) => {
    e.preventDefault(); setCreating(true);
    try {
      const project = await apiPost<Project>('/api/v1/projects', { name: newName, description: newDesc });
      setProjects((p) => [project, ...p]); setNewName(''); setNewDesc(''); setShowNew(false);
    } catch (err) { alert(err instanceof Error ? err.message : 'Failed'); }
    finally { setCreating(false); }
  };

  if (authLoading) return (
    <div className="flex items-center justify-center h-full">
      <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>
    </div>
  );
  if (!user) return (
    <div className="flex items-center justify-center h-full">
      <p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to view dashboard.</p>
    </div>
  );
  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>
    </div>
  );

  const statCards = overview ? [
    { label: 'Memories', value: overview.total_memories, icon: <Brain size={16} /> },
    { label: 'Sources', value: overview.total_sources, icon: <Database size={16} /> },
    { label: 'Sessions', value: overview.total_sessions, icon: <MessageSquare size={16} /> },
    { label: 'Facts', value: overview.total_facts, icon: <ShieldCheck size={16} /> },
    { label: 'Decisions', value: overview.total_decisions, icon: <Activity size={16} /> },
    { label: 'Graph Nodes', value: overview.total_graph_nodes, icon: <GitBranch size={16} /> },
  ] : [];

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">
            {workspace?.name || 'Dashboard'}
          </h1>
          <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">
            {projects.length} project{projects.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-[var(--sv-accent)] hover:bg-[var(--sv-accent-hover)] text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
        >
          <Plus size={16} /> New Project
        </button>
      </div>

      {/* New Project Form */}
      {showNew && (
        <form onSubmit={createProject} className="rounded-lg border border-[var(--sv-border-default)] bg-[var(--sv-bg-raised)] p-4 space-y-3 animate-slide-up">
          <div className="flex gap-3">
            <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Project name" required
              className="flex-1 bg-[var(--sv-bg-primary)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" />
            <input type="text" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} placeholder="Description (optional)"
              className="flex-1 bg-[var(--sv-bg-primary)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" />
            <div className="flex gap-2">
              <button type="submit" disabled={creating} className="bg-[var(--sv-accent)] text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 transition-opacity">
                {creating ? 'Creating…' : 'Create'}
              </button>
              <button type="button" onClick={() => setShowNew(false)} className="text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] px-4 py-2 rounded-md text-sm transition-colors">Cancel</button>
            </div>
          </div>
        </form>
      )}

      {/* Stats Grid */}
      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {statCards.map((card) => (
            <StatCard key={card.label} {...card} loading={loading} />
          ))}
        </div>
      )}

      {/* View Tabs */}
      <div className="flex items-center gap-1 bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-0.5 w-fit">
        {(['overview', 'recent'] as View[]).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${view === v ? 'bg-[var(--sv-accent)] text-white' : 'text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)]'}`}
          >
            {v === 'overview' ? 'Projects' : 'Recent Activity'}
          </button>
        ))}
      </div>

      {/* Project Grid */}
      {view === 'overview' && (
        projects.length === 0 ? (
          <div className="text-center py-20">
            <FolderOpen size={48} className="mx-auto text-[var(--sv-text-tertiary)] mb-4" />
            <p className="text-sm text-[var(--sv-text-tertiary)]">No projects yet.</p>
            <p className="text-xs text-[var(--sv-text-tertiary)] mt-1">Create your first project to get started.</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((p) => (
              <Link key={p.id} href={`/projects/${p.id}`}
                className="block rounded-lg border border-[var(--sv-border-default)] bg-[var(--sv-bg-raised)] p-5 hover:border-[var(--sv-accent)]/50 hover:shadow-[0_0_0_1px_var(--sv-accent)] transition-all duration-[var(--sv-duration-fast)] group">
                <div className="flex items-start justify-between">
                  <h3 className="font-medium text-sm text-[var(--sv-text-primary)] group-hover:text-[var(--sv-accent)] transition-colors">{p.name}</h3>
                  {p.created_at && <Badge variant="muted" size="sm">Project</Badge>}
                </div>
                {p.description && <p className="text-xs text-[var(--sv-text-tertiary)] mt-2 line-clamp-2">{p.description}</p>}
                <div className="mt-4 flex items-center gap-2">
                  <Link href={`/projects/${p.id}/chat`} className="text-xs text-[var(--sv-text-tertiary)] hover:text-[var(--sv-accent)] transition-colors">Chat</Link>
                  <span className="text-[var(--sv-border-subtle)]">·</span>
                  <Link href={`/projects/${p.id}/ingest`} className="text-xs text-[var(--sv-text-tertiary)] hover:text-[var(--sv-accent)] transition-colors">Ingest</Link>
                  <span className="text-[var(--sv-border-subtle)]">·</span>
                  <Link href={`/projects/${p.id}/memory`} className="text-xs text-[var(--sv-text-tertiary)] hover:text-[var(--sv-accent)] transition-colors">Memory</Link>
                </div>
              </Link>
            ))}
          </div>
        )
      )}

      {/* Recent Activity */}
      {view === 'recent' && overview && (
        <div className="rounded-lg border border-[var(--sv-border-default)] bg-[var(--sv-bg-raised)] divide-y divide-[var(--sv-border-subtle)]">
          <div className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock size={14} className="text-[var(--sv-text-tertiary)]" />
              <span className="text-sm font-medium text-[var(--sv-text-primary)]">Last 7 days</span>
            </div>
            <div className="flex gap-3">
              <Tooltip text="New memories in the last 7 days">
                <span className="text-xs text-[var(--sv-text-tertiary)]">{overview.recent_memories} memories</span>
              </Tooltip>
              <Tooltip text="New sessions in the last 7 days">
                <span className="text-xs text-[var(--sv-text-tertiary)]">{overview.recent_sessions} sessions</span>
              </Tooltip>
            </div>
          </div>
          {overview.recent_memories === 0 && overview.recent_sessions === 0 && (
            <div className="p-6 text-center">
              <p className="text-sm text-[var(--sv-text-tertiary)]">No recent activity.</p>
              <p className="text-xs text-[var(--sv-text-tertiary)] mt-1">Start a chat or ingest content to see activity here.</p>
            </div>
          )}
          {overview.memory_types && Object.keys(overview.memory_types).length > 0 && (
            <div className="p-4">
              <p className="text-xs font-medium text-[var(--sv-text-tertiary)] uppercase tracking-wider mb-3">Memory Distribution</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(overview.memory_types).map(([type, count]) => (
                  <Badge key={type} variant="accent" size="sm">{type}: {count}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
