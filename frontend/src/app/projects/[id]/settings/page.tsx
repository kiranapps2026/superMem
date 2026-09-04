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
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api';
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

  // Sync local state when project loads
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

  if (loading) return <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>;
  if (!project) return <div className="flex items-center justify-center h-full"><p className="text-sm text-gray-500">Project not found.</p></div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center gap-3 mb-6">
        <Settings size={20} className="text-gray-400" />
        <div>
          <h1 className="text-xl font-semibold">Project Settings</h1>
          <p className="text-sm text-gray-500">{project.name}</p>
        </div>
      </div>

      {message && (
        <ErrorAlert
          title={message.type === 'success' ? 'Success' : 'Error'}
          message={message.text}
          onDismiss={() => setMessage(null)}
        />
      )}

      <div className="flex gap-1 mb-6 border-b border-[var(--border)]">
        {(['general', 'members', 'danger'] as Tab[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm border-b-2 transition-colors capitalize ${activeTab === tab ? 'border-[var(--accent)] text-white' : 'border-transparent text-gray-400 hover:text-white'}`}
          >
            {tab === 'danger' ? 'Danger Zone' : tab}
          </button>
        ))}
      </div>

      {activeTab === 'general' && (
        <Card title="General" subtitle="Update project details">
          <form onSubmit={saveGeneral} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Project name</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                required
                className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Description</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={3}
                className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
            <button type="submit" disabled={saving} className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-2 rounded-md text-sm disabled:opacity-50 transition-colors">
              {saving ? 'Saving…' : 'Save changes'}
            </button>
          </form>
        </Card>
      )}

      {activeTab === 'members' && (
        <Card title="Members" subtitle={`${members.length} members`}>
          {membersLoading ? (
            <div className="py-4"><LoadingSpinner /></div>
          ) : members.length === 0 ? (
            <EmptyState icon={<Users size={20} />} title="No members" description="Members will appear here when they join." />
          ) : (
            <div className="divide-y divide-[var(--border)]">
              {members.map(m => (
                <div key={m.id} className="flex items-center gap-3 py-3">
                  <div className="w-8 h-8 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center shrink-0">
                    <span className="text-xs font-medium text-gray-400">{(m.user_name || m.user_email).charAt(0).toUpperCase()}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{m.user_name || m.user_email}</p>
                    <p className="text-xs text-gray-500">{m.user_email}</p>
                  </div>
                  <Badge variant="purple">{m.role}</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {activeTab === 'danger' && (
        <Card title="Danger Zone">
          <div className="space-y-4">
            <p className="text-sm text-gray-400">
              Once you delete a project, there is no going back. All data including memories, facts, decisions, and ingested sources will be permanently removed.
            </p>
            <button
              onClick={() => setShowDelete(true)}
              className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 px-4 py-2 rounded-md text-sm transition-colors"
            >
              <Trash2 size={14} /> Delete this project
            </button>
          </div>
        </Card>
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
