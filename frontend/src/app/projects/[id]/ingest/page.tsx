'use client';
import { useEffect, useState, useRef } from 'react';
import { IngestJobDetail } from '@/types/api';
import { apiGet, apiPost } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { Upload, CheckCircle, XCircle, Loader, FileText } from 'lucide-react';

const STATUS_STYLES: Record<string, { icon: React.ReactNode; color: string }> = {
  pending: { icon: <FileText size={16} />, color: 'text-gray-500' },
  processing: { icon: <Loader size={16} className="animate-spin" />, color: 'text-blue-400' },
  embedded: { icon: <Loader size={16} className="animate-spin" />, color: 'text-blue-400' },
  completed: { icon: <CheckCircle size={16} />, color: 'text-green-400' },
  failed: { icon: <XCircle size={16} />, color: 'text-red-400' },
  partial_failure: { icon: <XCircle size={16} />, color: 'text-yellow-400' },
};

export default function IngestPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [jobs, setJobs] = useState<IngestJobDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!user) return;
    apiGet<IngestJobDetail[]>('/api/v1/projects/' + projectId + '/ingest/jobs').then((j) => { setJobs(j); setLoading(false); }).catch(() => setLoading(false));
    const interval = setInterval(() => apiGet<IngestJobDetail[]>('/api/v1/projects/' + projectId + '/ingest/jobs').then((j) => setJobs(j)).catch(() => {}), 5000);
    return () => clearInterval(interval);
  }, [user, projectId]);

  const uploadFile = async () => {
    if (!file) return; setUploading(true);
    try {
      await apiPost('/api/v1/ingest/upload', { project_id: projectId, filename: file.name, content_type: file.type });
      setFile(null); if (fileRef.current) fileRef.current.value = '';
    } catch (err) { alert(err instanceof Error ? err.message : 'Upload failed'); }
    finally { setUploading(false); }
  };

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-1">Ingest</h1>
      <p className="text-sm text-gray-500 mb-6">Upload conversations for M0-M5 processing</p>
      <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 mb-6">
        <input ref={fileRef} type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} accept=".txt,.json,.csv,.md" className="hidden" />
        <div className="flex items-center gap-3">
          <button onClick={() => fileRef.current?.click()} className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-3 py-1.5 rounded-md text-sm">
            <Upload size={16} /> Select File
          </button>
          {file && <span className="text-sm text-gray-400">{file.name}</span>}
          {file && (
            <button onClick={uploadFile} disabled={uploading} className="bg-green-600 hover:bg-green-500 text-white px-3 py-1.5 rounded-md text-sm disabled:opacity-50">
              {uploading ? 'Uploading…' : 'Upload'}
            </button>
          )}
        </div>
      </div>
      <div className="space-y-2">
        {jobs.length === 0 && <p className="text-sm text-gray-500">No ingestion jobs yet.</p>}
        {jobs.map((job) => {
          const style = STATUS_STYLES[job.status] || STATUS_STYLES.pending;
          return (
            <div key={job.job_id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3 flex items-center gap-3">
              <div className={style.color}>{style.icon}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{job.source_type} &mdash; {job.job_id.slice(0, 8)}</p>
                <p className="text-xs text-gray-500">Stage: {job.stage || '—'} &middot; Records: {job.estimated_records ?? '—'}</p>
                {job.status === 'processing' || job.status === 'embedded' ? (
                  <div className="mt-1.5 h-1 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                    <div className="h-full bg-[var(--accent)] rounded-full transition-all" style={{ width: `${job.progress * 100}%` }} />
                  </div>
                ) : null}
              </div>
              <span className={`text-xs ${style.color}`}>{job.status}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}