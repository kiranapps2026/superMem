'use client';
import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { apiGet } from '@/lib/api';
import { ProvenanceOut } from '@/types/api';
import { useParams } from 'next/navigation';
import { GitBranch, ChevronRight, MessageSquare, Clock } from 'lucide-react';

export default function ProvenancePage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [records, setRecords] = useState<ProvenanceOut[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const data = await apiGet<ProvenanceOut[]>(`/api/v1/provenance/?project_id=${projectId}`);
      setRecords(data);
    } catch {}
    finally { setLoading(false); }
  }, [user, projectId]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-1">Provenance</h1>
      <p className="text-sm text-gray-500 mb-6">{records.length} traced responses</p>

      {records.length === 0 ? (
        <div className="text-center py-20">
          <GitBranch size={40} className="mx-auto text-gray-600 mb-3" />
          <p className="text-gray-500 text-sm">No provenance records yet. Chat in the project to generate traces.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {records.map((r) => (
            <div key={r.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 hover:border-[var(--accent)]/30 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <MessageSquare size={14} className="text-gray-500" />
                  <span className="text-sm font-medium">{r.model}</span>
                  <span className="text-xs text-gray-500">via {r.provider}</span>
                </div>
                <span className="text-xs text-gray-500">{new Date(r.created_at).toLocaleString()}</span>
              </div>

              <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-2">
                <span className="flex items-center gap-1"><Clock size={12} />{r.latency_ms}ms</span>
                <span>Tokens: {r.total_tokens}</span>
                <span>Method: {r.retrieval_method}</span>
                {r.confidence != null && <span className={r.confidence >= 0.7 ? 'text-green-400' : r.confidence >= 0.4 ? 'text-yellow-400' : 'text-red-400'}>Confidence: {Math.round(r.confidence * 100)}%</span>}
              </div>

              {r.memory_ids_used && r.memory_ids_used.length > 0 && (
                <div className="flex items-center gap-1.5 mt-2">
                  <span className="text-xs text-gray-500">Memory sources:</span>
                  {r.memory_ids_used.slice(0, 5).map((mid, i) => (
                    <span key={i} className="text-xs bg-[var(--bg-tertiary)] px-1.5 py-0.5 rounded text-gray-400 font-mono">{mid.slice(0, 8)}</span>
                  ))}
                  {r.memory_ids_used.length > 5 && <span className="text-xs text-gray-500">+{r.memory_ids_used.length - 5} more</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
