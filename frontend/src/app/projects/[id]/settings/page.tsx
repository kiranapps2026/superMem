'use client';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useParams, useRouter } from 'next/navigation';
import {
  Card, Badge, EmptyState, ErrorAlert, LoadingSpinner,
  ConfirmDialog, useClipboard
} from '@/components/ui';
import { Settings, Trash2, Check, X, Copy, RefreshCw, Shield, Users } from 'lucide-react';
import { useProject, useUpdateProject, useDeleteProject } from '@/features/projects/useProjects';
import { apiGet } from '@/lib/api';
import { WorkspaceMemberOut } from '@/types/api';

type Tab = 'general' | 'members' | 'danger';

export default function ProjectSettingsPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const router = useRouter();
  const { project, loading, error, reload } = useProject(projectId);
  const { update, loading: saving } = useUpdateProject(projectId);
  const { remove, loading: deleting } = useDeleteProject();

  const [activeTab, setActiveTab] = useState<Tab>('general');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showDelete, setShowDelete] = useState(false);
  const [members, setMembers] = useState<WorkspaceMemberOut[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const { copied: copiedKey, copy } = useClipboard({ timeout: 3000 });

  useEffect(() => {
    if (project) {
      setName(project.name);
      setDescription(project.description || '');
    }
  }, [project]);

  const loadMembers = useCallback(async () => {
    setMembersLoading(true);
    try {
      const data = await apiGet<WorkspaceMemberOut[]>('/api/v1/workspace/members');
      setMembers(data);
    } catch {}
    finally { setMembersLoading(false); }
  }, []);

  useEffect(() => {
    if (activeTab === 'members') loadMembers();
  }, [activeTab, loadMembers]);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const saveGeneral = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const updated = await update({ name, description: description || null });
      if (updated) {
        showMessage('success', 'Project updated');
        await reload();
      }
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed to save');
    }
  };

  const confirmDelete = async () => {
    try {
      const ok = await remove(projectId);
      if (ok) router.push('/projects');
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed to delete');
    } finally {
      setShowDelete(false);
    }
  };

  const ROLE_VARIANTS: Record<string, string> = {
    owner: 'purple', admin: 'warning', member: 'default', viewer: 'info',
  };

  if (loading) return <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>;
  if (!project) return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Project not found.</p></div>;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3">
        <Settings size={20} className="text-[var(--sv-text-tertiary)]" />
        <div>
          <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Project Settings</h1>
          <p className="text-sm text-[var(--sv-text-tertiary)]">{project.name}</p>
        </div>
      </div>

      {message && (
        <ErrorAlert
          title={message.type === 'success' ? 'Success' : 'Error'}
          message={message.text}
          onDismiss={() => setMessage(null)}
        />
      )}

      <div className="flex gap-1 mb-6 border-b border-[var(--sv-border-default)]">
        {(['general', 'members', 'danger'] as Tab[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm border-b-2 transition-colors capitalize ${activeTab === tab ? 'border-[var(--sv-accent)] text-[var(--sv-text-primary)]' : 'border-transparent text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)]'}`}
          >
            {tab === 'danger' ? 'Danger Zone' : tab}
          </button>
        ))}
      </div>

      {activeTab === 'general' && (
        <div className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-5">
          <h2 className="text-sm font-medium text-[var(--sv-text-primary)] mb-4">General</h2>
          <form onSubmit={saveGeneral} className="space-y-4">
            <div>
              <label className="block text-xs text-[var(--sv-text-tertiary)] mb-1">Project name</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                required
                className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--sv-text-tertiary)] mb-1">Description</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={3}
                className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors resize-none"
              />
            </div>
            <button type="submit" disabled={saving} className="bg-[var(--sv-accent)] hover:bg-[var(--sv-accent-hover)] text-[var(--sv-text-inverse)] px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 transition-colors">
              {saving ? 'Saving…' : 'Save changes'}
            </button>
          </form>
        </div>
      )}

      {activeTab === 'members' && (
        <div className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg overflow-hidden">
          <div className="px-5 py-3 border-b border-[var(--sv-border-subtle)]">
            <h2 className="text-sm font-medium text-[var(--sv-text-primary)]">Members ({members.length})</h2>
          </div>
          {membersLoading ? (
            <div className="py-4"><LoadingSpinner /></div>
          ) : members.length === 0 ? (
            <EmptyState icon={<Users size={20} />} title="No members" description="Members will appear here when they join." />
          ) : (
            <div className="divide-y divide-[var(--sv-border-subtle)]">
              {members.map(m => (
                <div key={m.id} className="flex items-center gap-3 px-5 py-3">
                  <div className="w-8 h-8 rounded-full bg-[var(--sv-bg-overlay)] border border-[var(--sv-border-subtle)] flex items-center justify-center shrink-0">
                    <span className="text-xs font-medium text-[var(--sv-text-tertiary)]">{(m.user_name || m.user_email).charAt(0).toUpperCase()}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[var(--sv-text-primary)] truncate">{m.user_name || m.user_email}</p>
                    <p className="text-xs text-[var(--sv-text-tertiary)]">{m.user_email}</p>
                  </div>
                  <Badge category="authority" value={m.role.toUpperCase()} variant={ROLE_VARIANTS[m.role] || 'default'} size="sm" />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'danger' && (
        <div className="bg-[var(--sv-error)]/5 border border-[var(--sv-error)]/20 rounded-lg p-5">
          <h2 className="text-sm font-medium text-[var(--sv-error)] mb-4">Danger Zone</h2>
          <p className="text-sm text-[var(--sv-text-tertiary)] mb-4">
            Once you delete a project, there is no going back. All data including memories, facts, decisions, and ingested sources will be permanently removed.
          </p>
          <button
            onClick={() => setShowDelete(true)}
            className="flex items-center gap-2 bg-[var(--sv-error)]/10 border border-[var(--sv-error)]/30 text-[var(--sv-error)] hover:bg-[var(--sv-error)]/20 px-4 py-2 rounded-md text-sm font-medium transition-colors"
          >
            <Trash2 size={14} /> Delete this project
          </button>
        </div>
      )}

      <ConfirmDialog
        open={showDelete}
        title="Delete Project"
        description={`Permanently delete "${project.name}" and all its data? This action cannot be undone.`}
        confirmLabel="Delete"
        danger
        onConfirm={confirmDelete}
        onCancel={() => setShowDelete(false)}
      />
    </div>
  );
}
