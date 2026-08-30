'use client';
import { useEffect, useState, useRef } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { apiGet } from '@/lib/api';
import { MemoryItemOut } from '@/types/api';
import { useParams } from 'next/navigation';
import { GitBranch, Plus, Search as SearchIcon } from 'lucide-react';

export default function MemoryPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [items, setItems] = useState<MemoryItemOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState('');
  const pageSize = 50;

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    apiGet(`/api/v1/memory?project_id=${projectId}&page=${page}&page_size=${pageSize}${filter ? `&type=${encodeURIComponent(filter)}` : ''}`).then((r: any) => {
      setItems(r.items); setTotal(r.total); setLoading(false);
    }).catch(() => setLoading(false));
  }, [user, projectId, page, filter]);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Memory</h1>
          <p className="text-sm text-gray-500">{total} items</p>
        </div>
        <div className="flex items-center gap-3">
          <input value={filter} onChange={(e) => { setFilter(e.target.value); setPage(1); }}
            placeholder="Filter by type…" className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:border-[var(--accent)]" />
        </div>
      </div>
      {loading ? <div className="text-sm text-gray-500">Loading…</div> : items.length === 0 ? (
        <p className="text-sm text-gray-500">No memory items yet. Ingest sessions to populate memory.</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium bg-[var(--bg-tertiary)] px-2 py-0.5 rounded">{item.type}</span>
                <span className="text-xs text-gray-500">{new Date(item.created_at).toLocaleString()}</span>
              </div>
              <p className="text-sm text-gray-300 line-clamp-3">{item.content}</p>
              {item.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {item.tags.map((t) => <span key={t} className="text-xs text-gray-500 bg-[var(--bg-tertiary)] px-1.5 py-0.5 rounded">{t}</span>)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}