'use client';
import { useEffect, useState, useCallback, useRef } from 'react';
import { apiGet, apiPost, uploadFile } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { Upload, CheckCircle, XCircle, Loader, FileText, Trash2, RefreshCw } from 'lucide-react';

const STATUS_STYLES: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  queued: { icon: <FileText size={16} />, color: 'text-gray-400', label: 'Queued' },
  processing: { icon: <Loader size={16} className="animate-spin" />, color: 'text-blue-400', label: 'Processing' },
  completed: { icon: <CheckCircle size={16} />, color: 'text-green-400', label: 'Completed' },
  failed: { icon: <XCircle size={16} />, color: 'text-red-400', label: 'Failed' },
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
  const fileRef = useRef<HTMLInputElement>(null);

  const loadSources = useCallback(async () => {
    if (!user) return;
    try {
      const data = await apiGet<{ items: any[] }>(`/api/v1/ingest/sources?project_id=${encodeURIComponent(projectId)}&limit=50`);
      setSources(data.items || []);
    } catch {}
    finally { setLoading(false); }
  }, [user, projectId]);

  useEffect(() => { loadSources(); }, [loadSources]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;
    setUploading(true);
    setUploadProgress(0);
    try {
      const result = await uploadFile(projectId, file, (p) => setUploadProgress(Math.round(p * 100)));
      setUploadProgress(0);
      await loadSources();
    } catch (err) { alert(err instanceof Error ? err.message : 'Upload failed'); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ''; }
  };

  const handleTextUpload = async () => {
    if (!rawContent.trim() || !user) return;
    setUploading(true);
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
    } catch (err) { alert(err instanceof Error ? err.message : 'Upload failed'); }
    finally { setUploading(false); }
  };

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-1">Ingest</h1>
      <p className="text-sm text-gray-500 mb-6">Import AI conversations for M0-M5 processing</p>

      {/* Upload form */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 mb-6 space-y-3">
        <div className="flex gap-3">
          <div className="flex-1">
            <label className="block text-xs text-gray-400 mb-1">Source type</label>
            <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}
              className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]">
              <option value="text">Plain text</option>
              <option value="chatgpt">ChatGPT export</option>
              <option value="jsonl">JSONL</option>
              <option value="markdown">Markdown</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-xs text-gray-400 mb-1">Title (optional)</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Conversation title"
              className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]" />
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">Content</label>
          <textarea value={rawContent} onChange={(e) => setRawContent(e.target.value)} rows={4}
            placeholder="Paste conversation text here…"
            className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm resize-none focus:outline-none focus:border-[var(--accent)]" />
        </div>

        <div className="flex items-center gap-3">
          <input ref={fileRef} type="file" onChange={handleFileUpload} accept=".txt,.json,.jsonl,.md,.csv" disabled={uploading}
            className="text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-sm file:bg-[var(--bg-tertiary)] file:text-gray-300 hover:file:bg-[var(--accent)]/20 disabled:opacity-50" />
          <button onClick={handleTextUpload} disabled={uploading || !rawContent.trim()}
            className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-1.5 rounded-md text-sm font-medium disabled:opacity-50 transition-colors">
            {uploading ? 'Processing…' : 'Upload & Process'}
          </button>
        </div>
        {uploading && uploadProgress > 0 && (
          <div className="h-1 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
            <div className="h-full bg-[var(--accent)] rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
          </div>
        )}
      </div>

      {/* Source list */}
      <div className="space-y-2">
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Recent sources</p>
        {sources.length === 0 && (
          <div className="text-center py-12 bg-[var(--bg-secondary)] border border-[var(--border)] border-dashed rounded-lg">
            <Upload size={24} className="mx-auto text-gray-600 mb-2" />
            <p className="text-sm text-gray-500">No sources yet. Upload a conversation to get started.</p>
          </div>
        )}
        {sources.map((s) => {
          const style = STATUS_STYLES[s.status] || STATUS_STYLES.queued;
          return (
            <a key={s.id} href={`/projects/${projectId}/sessions`} className="flex items-center gap-3 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3.5 hover:border-[var(--accent)]/30 transition-colors">
              <div className={style.color}>{style.icon}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium truncate">{s.title || s.source_type}</p>
                  <span className={`text-xs ${style.color}`}>{style.label}</span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  {s.source_type} {s.message_count ? `· ${s.message_count} messages` : ''} · {s.created_at ? new Date(s.created_at).toLocaleDateString() : ''}
                </p>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
