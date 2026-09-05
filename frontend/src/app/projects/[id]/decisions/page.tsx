'use client';
import { useEffect, useState, useCallback } from 'react';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { CheckSquare } from 'lucide-react';
import { DecisionItem } from '@/types/api';

export default function DecisionsPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [decisions, setDecisions] = useState<DecisionItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!user) return;
    try {
      const data = await apiGet<{ items: DecisionItem[] }>(`/api/v1/ingest/decisions?project_id=${encodeURIComponent(projectId)}`);
      setDecisions(data.items || []);
    } catch {}
    finally { setLoading(false); }
  }, [user, projectId]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-1">Decisions</h1>
      <p className="text-sm text-gray-500 mb-4">{decisions.length} decisions</p>
      {decisions.length === 0 ? <p className="text-sm text-gray-500">No decisions yet. Ingest conversations to extract decisions.</p> : (
        <div className="space-y-2">
          {decisions.map((d) => (
            <div key={d.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
              <div className="flex items-start justify-between">
                <p className="text-sm">{d.content}</p>
                <span className={`text-xs shrink-0 ml-2 ${d.confidence >= 0.8 ? 'text-green-400' : d.confidence >= 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>{Math.round(d.confidence * 100)}%</span>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded ${d.temporal_status === 'current' ? 'bg-green-400/10 text-green-400' : 'bg-yellow-400/10 text-yellow-400'}`}>{d.temporal_status}</span>
                {d.authority != null && <span className="text-xs text-gray-500">authority: {d.authority}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
