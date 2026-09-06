'use client';
import { useEffect, useState, useCallback, FormEvent } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { apiGet, apiPatch, apiDelete, apiPost } from '@/lib/api';
import { WorkspaceDetail, WorkspaceMemberOut, InvitationOut } from '@/types/api';
import {
  User, Shield, Mail, Users, Trash2,
  UserPlus, X, Clock, Save, ArrowLeft
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';

type Tab = 'workspace' | 'members' | 'invitations';

const ROLE_VARIANTS: Record<string, string> = {
  owner: 'purple',
  admin: 'warning',
  member: 'default',
  viewer: 'info',
};
const ROLE_ORDER = ['owner', 'admin', 'member', 'viewer'];

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('workspace');
  const [workspace, setWorkspace] = useState<WorkspaceDetail | null>(null);
  const [members, setMembers] = useState<WorkspaceMemberOut[]>([]);
  const [invitations, setInvitations] = useState<InvitationOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUserRole, setCurrentUserRole] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [inviting, setInviting] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);

  const canManage = currentUserRole === 'owner' || currentUserRole === 'admin';
  const isOwner = currentUserRole === 'owner';

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const loadData = useCallback(async () => {
    try {
      const [ws, mems] = await Promise.all([
        apiGet<WorkspaceDetail>('/api/v1/workspace'),
        apiGet<WorkspaceMemberOut[]>('/api/v1/workspace/members'),
      ]);
      setWorkspace(ws);
      setMembers(mems);
      const me = mems.find(m => m.user_id === user?.id);
      if (me) setCurrentUserRole(me.role);
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  const loadInvitations = useCallback(async () => {
    try {
      const data = await apiGet<InvitationOut[]>('/api/v1/workspace/members/invitations');
      setInvitations(data);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);
  useEffect(() => { if (activeTab === 'invitations') loadInvitations(); }, [activeTab, loadInvitations]);

  const saveWorkspace = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget as HTMLFormElement);
    const name = fd.get('name') as string;
    const description = fd.get('description') as string;
    setSaving(true);
    try {
      const updated = await apiPatch<WorkspaceDetail>('/api/v1/workspace', { name, description: description || null });
      setWorkspace(updated);
      showMessage('success', 'Workspace updated');
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed to save');
    } finally { setSaving(false); }
  };

  const inviteMember = async (e: FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const fd = new FormData(form);
    setInviting(true);
    try {
      await apiPost('/api/v1/workspace/members', { email: fd.get('email'), role: fd.get('role') });
      form.reset();
      showMessage('success', 'Invitation sent');
      await loadData();
      await loadInvitations();
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed to invite');
    } finally { setInviting(false); }
  };

  const changeRole = async (memberId: string, newRole: string) => {
    try {
      const updated = await apiPatch<WorkspaceMemberOut>(`/api/v1/workspace/members/${memberId}`, { role: newRole });
      setMembers((ms) => ms.map(m => m.id === memberId ? { ...m, role: updated.role } : m));
      showMessage('success', 'Role updated');
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed');
    }
  };

  const removeMember = async (memberId: string, memberEmail: string) => {
    if (!confirm(`Remove ${memberEmail} from this workspace?`)) return;
    setRemovingId(memberId);
    try {
      await apiDelete(`/api/v1/workspace/members/${memberId}`);
      setMembers((ms) => ms.filter(m => m.id !== memberId));
      showMessage('success', 'Member removed');
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed to remove');
    } finally { setRemovingId(null); }
  };

  const revokeInvitation = async (id: string) => {
    if (!confirm('Revoke this invitation?')) return;
    try {
      await apiDelete(`/api/v1/workspace/members/invitation/${id}`);
      setInvitations((inv) => inv.filter(i => i.id !== id));
      showMessage('success', 'Invitation revoked');
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div></div>;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Settings</h1>
        <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">{workspace?.name || 'Workspace'}</p>
      </div>

      {message && (
        <div className={`px-4 py-2.5 rounded-lg text-sm ${message.type === 'error' ? 'bg-[var(--sv-error)]/10 border border-[var(--sv-error)]/30 text-[var(--sv-error)]' : 'bg-[var(--sv-success)]/10 border border-[var(--sv-success)]/30 text-[var(--sv-success)]'}`}>
          {message.text}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[var(--sv-border-default)]">
        {([
          { key: 'workspace', label: 'Workspace', icon: Shield },
          { key: 'members', label: `Members (${members.length})`, icon: Users },
          { key: 'invitations', label: 'Invitations', icon: Mail },
        ] as { key: Tab; label: string; icon: any }[]).map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm border-b-2 transition-colors flex items-center gap-2 ${activeTab === tab.key ? 'border-[var(--sv-accent)] text-[var(--sv-text-primary)]' : 'border-transparent text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)]'}`}>
            <tab.icon size={14} />{tab.label}
          </button>
        ))}
      </div>

      {/* Workspace tab */}
      {activeTab === 'workspace' && (
        <div className="space-y-6">
          <section>
            <div className="flex items-center gap-2 mb-3"><Shield size={16} className="text-[var(--sv-text-tertiary)]" /><h2 className="font-medium text-sm text-[var(--sv-text-primary)]">Workspace Details</h2></div>
            <form onSubmit={saveWorkspace} className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-5 space-y-4">
              <div>
                <label className="block text-xs text-[var(--sv-text-tertiary)] mb-1">Name</label>
                <input name="name" defaultValue={workspace?.name || ''} required
                  className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" />
              </div>
              <div>
                <label className="block text-xs text-[var(--sv-text-tertiary)] mb-1">Description</label>
                <textarea name="description" defaultValue={workspace?.description || ''} rows={3}
                  className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors resize-none" />
              </div>
              <button type="submit" disabled={saving} className="bg-[var(--sv-accent)] hover:bg-[var(--sv-accent-hover)] text-[var(--sv-text-inverse)] px-4 py-1.5 rounded-md text-sm font-medium disabled:opacity-50 transition-colors flex items-center gap-1.5">
                <Save size={14} /> {saving ? 'Saving…' : 'Save changes'}
              </button>
            </form>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3"><User size={16} className="text-[var(--sv-text-tertiary)]" /><h2 className="font-medium text-sm text-[var(--sv-text-primary)]">Profile</h2></div>
            <div className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-5 space-y-3">
              <div><label className="block text-xs text-[var(--sv-text-tertiary)] mb-1">Email</label><p className="text-sm text-[var(--sv-text-primary)]">{user?.email}</p></div>
              <div><label className="block text-xs text-[var(--sv-text-tertiary)] mb-1">Name</label><p className="text-sm text-[var(--sv-text-primary)]">{user?.name || '—'}</p></div>
              <div><label className="block text-xs text-[var(--sv-text-tertiary)] mb-1">Role</label><p className="text-sm text-[var(--sv-text-primary)] capitalize">{currentUserRole}</p></div>
            </div>
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3"><Shield size={16} className="text-[var(--sv-text-tertiary)]" /><h2 className="font-medium text-sm text-[var(--sv-text-primary)]">Password</h2></div>
            <form onSubmit={async (e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget as HTMLFormElement);
              try {
                await apiPost('/api/v1/auth/change-password', { current_password: fd.get('current') as string, new_password: fd.get('new') as string });
                showMessage('success', 'Password updated');
                e.currentTarget.reset();
              } catch (err) {
                showMessage('error', err instanceof Error ? err.message : 'Failed');
              }
            }} className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-5 space-y-4">
              <div>
                <label className="block text-xs text-[var(--sv-text-tertiary)] mb-1">Current password</label>
                <input name="current" type="password" required
                  className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" />
              </div>
              <div>
                <label className="block text-xs text-[var(--sv-text-tertiary)] mb-1">New password</label>
                <input name="new" type="password" required minLength={8}
                  className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" />
              </div>
              <button type="submit" className="bg-[var(--sv-accent)] hover:bg-[var(--sv-accent-hover)] text-[var(--sv-text-inverse)] px-4 py-1.5 rounded-md text-sm font-medium transition-colors">Update password</button>
            </form>
          </section>
        </div>
      )}

      {/* Members tab */}
      {activeTab === 'members' && (
        <div className="space-y-6">
          {canManage && (
            <section>
              <div className="flex items-center gap-2 mb-3"><Mail size={16} className="text-[var(--sv-text-tertiary)]" /><h2 className="font-medium text-sm text-[var(--sv-text-primary)]">Invite People</h2></div>
              <form onSubmit={inviteMember} className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-4">
                <div className="flex gap-3">
                  <input type="email" name="email" placeholder="colleague@example.com" required
                    className="flex-1 bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" />
                  <select name="role" className="bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors">
                    {ROLE_ORDER.filter(r => !(r === 'owner' && !isOwner)).map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                  <button type="submit" disabled={inviting} className="bg-[var(--sv-accent)] hover:bg-[var(--sv-accent-hover)] text-[var(--sv-text-inverse)] px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 transition-colors whitespace-nowrap flex items-center gap-1.5">
                    <UserPlus size={14} /> {inviting ? 'Sending…' : 'Invite'}
                  </button>
                </div>
              </form>
            </section>
          )}

          <section>
            <div className="flex items-center gap-2 mb-3"><Users size={16} className="text-[var(--sv-text-tertiary)]" /><h2 className="font-medium text-sm text-[var(--sv-text-primary)]">Members ({members.length})</h2></div>
            <div className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg overflow-hidden divide-y divide-[var(--sv-border-subtle)]">
              {members.map((m) => {
                const editable = canManage && m.user_id !== user?.id && m.role !== 'owner';
                const removable = canManage && m.user_id !== user?.id && (m.role !== 'owner' || isOwner) && m.role !== 'admin';
                return (
                  <div key={m.id} className="px-4 py-3 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-[var(--sv-bg-overlay)] border border-[var(--sv-border-subtle)] flex items-center justify-center shrink-0">
                      <span className="text-xs font-medium text-[var(--sv-text-tertiary)]">{(m.user_name || m.user_email).charAt(0).toUpperCase()}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[var(--sv-text-primary)] truncate">{m.user_name || m.user_email}</p>
                      <p className="text-xs text-[var(--sv-text-tertiary)]">{m.user_email}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge category="authority" value={m.role.toUpperCase()} variant={ROLE_VARIANTS[m.role] || 'default'} size="sm" />
                      {editable && (
                        <select
                          value={m.role}
                          onChange={(e) => changeRole(m.id, e.target.value)}
                          className="bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-1.5 py-0.5 text-xs text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors"
                        >
                          {ROLE_ORDER.filter(r => !(r === 'owner' && !isOwner)).map(r => <option key={r} value={r}>{r}</option>)}
                        </select>
                      )}
                      {removable && (
                        <button onClick={() => removeMember(m.id, m.user_email)} disabled={removingId === m.id}
                          className="p-1 rounded hover:bg-[var(--sv-error)]/10 text-[var(--sv-text-tertiary)] hover:text-[var(--sv-error)] disabled:opacity-50 transition-colors" title="Remove member">
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
              {members.length === 0 && <p className="text-sm text-[var(--sv-text-tertiary)] text-center py-8">No members yet.</p>}
            </div>
          </section>
        </div>
      )}

      {/* Invitations tab */}
      {activeTab === 'invitations' && (
        <section>
          <h2 className="text-sm font-medium text-[var(--sv-text-primary)] mb-3">Pending &amp; Past Invitations</h2>
          {invitations.length === 0 ? (
            <div className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] border-dashed rounded-lg p-8 text-center">
              <Mail size={24} className="mx-auto text-[var(--sv-text-disabled)] mb-2" />
              <p className="text-sm text-[var(--sv-text-tertiary)]">No invitations yet.</p>
            </div>
          ) : (
            <div className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg overflow-hidden divide-y divide-[var(--sv-border-subtle)]">
              {invitations.map((inv) => (
                <div key={inv.id} className="px-4 py-3 flex items-center gap-3">
                  <Mail size={14} className="text-[var(--sv-text-tertiary)] shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-[var(--sv-text-primary)] truncate">{inv.email}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge category="temporal" value={inv.state.toUpperCase()} size="sm" />
                      <span className="text-xs text-[var(--sv-text-tertiary)]">{inv.role}</span>
                      {inv.expires_at && (
                        <>
                          <span className="text-xs text-[var(--sv-text-disabled)]">·</span>
                          <span className="text-xs text-[var(--sv-text-disabled)] flex items-center gap-1"><Clock size={10} />{new Date(inv.expires_at).toLocaleDateString()}</span>
                        </>
                      )}
                    </div>
                  </div>
                  {inv.state === 'pending' && canManage && (
                    <button onClick={() => revokeInvitation(inv.id)} className="p-1 rounded hover:bg-[var(--sv-error)]/10 text-[var(--sv-text-tertiary)] hover:text-[var(--sv-error)] transition-colors" title="Revoke">
                      <X size={12} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
