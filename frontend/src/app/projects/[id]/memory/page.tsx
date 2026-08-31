'use client';
import { useEffect, useState, useCallback } from 'react';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';

export default function MemoryPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(0);

  const loadData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const url = `/api/v1/memory/?limit=50&offset=${page * 50}&project_id=${encodeURIComponent(projectId)}`;
      if (filter) {
        const data = await apiGet<any[]>(`/api/v1/memory/?limit=50&offset=${page * 50}&project_id=${encodeURIComponent(projectId)}&memory_type=${encodeURIComponent(filter)}`);
        setItems(data);
      } else {
        const data = await apiGet<any[]>(`/api/v1/memory/?limit=50&offset=${page * 50}&project_id=${encodeURIComponent(projectId)}`);
        setItems(data);
      }
    } catch {}
    finally { setLoading(false); }
  }, [user, projectId, filter, page]);

  useEffect(() => { loadData(); }, [loadData]);

  const tagsFor = (item: any): string[] => (item.extra_metadata?.tags as string[]) || [];

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Memory</h1>
          <p className="text-sm text-gray-500">{items.length} items</p>
        </div>
        <input value={filter} onChange={(e) => { setFilter(e.target.value); setPage(0); }}
          placeholder="Filter by type…" className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:border-[var(--accent)]" />
      </div>
      {loading ? <div className="text-sm text-gray-500">Loading…</div> : items.length === 0 ? (
        <p className="text-sm text-gray-500">No memory items yet. Ingest sessions to populate memory.</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium bg-[var(--bg-tertiary)] px-2 py-0.5 rounded">{item.memory_type}</span>
                <div className="flex items-center gap-2">
                  {item.temporal_status && <span className={`text-xs px-2 py-0.5 rounded ${item.temporal_status === 'current' ? 'bg-green-400/10 text-green-400' : 'bg-yellow-400/10 text-yellow-400'}`}>{item.temporal_status}</span>}
                  <span className="text-xs text-gray-500">{new Date(item.created_at).toLocaleString()}</span>
                </div>
              </div>
              <p className="text-sm text-gray-300 line-clamp-3">{item.content}</p>
              {tagsFor(item).length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {tagsFor(item).map((t: string) => <span key={t} className="text-xs text-gray-500 bg-[var(--bg-tertiary)] px-1.5 py-0.5 rounded">{t}</span>)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
