'use client';
import { useEffect, useState, useCallback, useRef } from 'react';
import { apiGet, apiPost, uploadFile } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { Upload, CheckCircle, XCircle, Loader2, FileText, Trash2, RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { ErrorAlert } from '@/components/ui/ErrorAlert';

const STATUS_MAP: Record<string, { icon: typeof Upload; color: string; label: string }> = {
  queued:     { icon: FileText, color: 'text-[var(--sv-text-tertiary)]', label: 'Queued' },
  processing: { icon: Loader2, color: 'text-[var(--sv-info)]', label: 'Processing' },
  completed:  { icon: CheckCircle, color: 'text-[var(--sv-success)]', label: 'Completed' },
  failed:     { icon: XCircle, color: 'text-[var(--sv-error)]', label: 'Failed' },
};

export default function IngestPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [rawContent, setRawContent] = useState('');
  const [sourceType, setSourceType] = useState('text');
  const [title, setTitle] = useState('');
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadSources = useCallback(async () => {
    if (!user) return;
    try {
      const data = await apiGet<{ items: any[] }>(`/api/v1/ingest/sources?project_id=${encodeURIComponent(projectId)}&limit=50`);
      setSources(data.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sources');
    } finally { setLoading(false); }
  }, [user, projectId]);

  useEffect(() => { loadSources(); }, [loadSources]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;
    setUploading(true);
    setUploadProgress(0);
    setError(null);
    try {
      const result = await uploadFile(projectId, file, (p) => setUploadProgress(Math.round(p * 100)));
      setUploadProgress(0);
      await loadSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally { setUploading(false); if (fileRef.current) fileRef.current.value = ''; }
  };

  const handleTextUpload = async () => {
    if (!rawContent.trim() || !user) return;
    setUploading(true);
    setError(null);
    try {
      await apiPost('/api/v1/ingest/upload', {
        project_id: projectId,
        source_type: sourceType,
        content: rawContent,
        title: title || undefined,
      });
      setRawContent('');
      setTitle('');
      setTimeout(loadSources, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally { setUploading(false); }
  };

  if (!user) return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to ingest.</p></div>;

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Ingest</h1>
        <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">Import AI conversations for M0–M5 processing</p>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {loading && <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>}

      {/* Upload form */}
      {!loading && (
        <div className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-4 space-y-3">
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-xs text-[var(--sv-text-tertiary)] mb-1 font-medium">Source type</label>
              <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}
                className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors">
                <option value="text">Plain text</option>
                <option value="chatgpt">ChatGPT export</option>
                <option value="claude">Claude export</option>
                <option value="jsonl">JSONL</option>
                <option value="markdown">Markdown</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-xs text-[var(--sv-text-tertiary)] mb-1 font-medium">Title (optional)</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Conversation title"
                className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] focus:outline-none focus:border-[var(--sv-accent)] transition-colors" />
            </div>
          </div>

          <div>
            <label className="block text-xs text-[var(--sv-text-tertiary)] mb-1 font-medium">Content</label>
            <textarea value={rawContent} onChange={(e) => setRawContent(e.target.value)} rows={4}
              placeholder="Paste conversation text here…"
              className="w-full bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-md px-3 py-2 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] resize-none focus:outline-none focus:border-[var(--sv-accent)] transition-colors" />
          </div>

          <div className="flex items-center gap-3">
            <input ref={fileRef} type="file" onChange={handleFileUpload} accept=".txt,.json,.jsonl,.md,.csv" disabled={uploading}
              className="text-sm text-[var(--sv-text-tertiary)] file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-sm file:bg-[var(--sv-bg-overlay)] file:text-[var(--sv-text-secondary)] hover:file:bg-[var(--sv-accent)]/20 disabled:opacity-50" />
            <button onClick={handleTextUpload} disabled={uploading || !rawContent.trim()}
              className="bg-[var(--sv-accent)] hover:bg-[var(--sv-accent-hover)] text-[var(--sv-text-inverse)] px-4 py-1.5 rounded-md text-sm font-medium disabled:opacity-50 transition-colors shrink-0">
              {uploading ? 'Processing…' : 'Upload & Process'}
            </button>
          </div>

          {uploading && uploadProgress > 0 && (
            <Progress value={uploadProgress} />
          )}
        </div>
      )}

      {/* Source list */}
      {!loading && (
        <div className="space-y-2">
          <p className="text-xs text-[var(--sv-text-tertiary)] uppercase tracking-wider font-medium">Recent sources</p>
          {sources.length === 0 && (
            <div className="text-center py-12 bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] border-dashed rounded-lg">
              <Upload size={24} className="mx-auto text-[var(--sv-text-disabled)] mb-2" />
              <p className="text-sm text-[var(--sv-text-tertiary)]">No sources yet. Upload a conversation to get started.</p>
            </div>
          )}
          {sources.map((s) => {
            const style = STATUS_MAP[s.status] || STATUS_MAP.queued;
            const Icon = style.icon;
            return (
              <a key={s.id} href={`/projects/${projectId}/sessions`} className="flex items-center gap-3 bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg p-3.5 hover:border-[var(--sv-accent)]/30 transition-colors">
                <div className={style.color}><Icon size={16} /></div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-[var(--sv-text-primary)] truncate">{s.title || s.source_type}</p>
                    <span className={`text-xs ${style.color} shrink-0 ml-2`}>{style.label}</span>
                  </div>
                  <p className="text-xs text-[var(--sv-text-tertiary)] mt-0.5">
                    {s.source_type} {s.message_count ? `· ${s.message_count} messages` : ''} · {s.created_at ? new Date(s.created_at).toLocaleDateString() : ''}
                  </p>
                </div>
              </a>
            );
          })}
        </div>
      )}
    </div>
  );
}
