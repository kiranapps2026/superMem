'use client';
import { useEffect, useState } from 'react';
import { DecisionInfo } from '@/types/api';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { CheckSquare } from 'lucide-react';

export default function DecisionsPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [decisions, setDecisions] = useState<DecisionInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    apiGet<DecisionInfo[]>(`/api/v1/memory/${projectId}/decisions`).then((d) => { setDecisions(d); setLoading(false); }).catch(() => setLoading(false));
  }, [user, projectId]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-1">Decisions</h1>
      <p className="text-sm text-gray-500 mb-4">{decisions.length} decisions</p>
      {decisions.length === 0 ? <p className="text-sm text-gray-500">No decisions yet.</p> : (
        <div className="space-y-2">
          {decisions.map((d) => (
            <div key={d.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4">
              <div className="flex items-start justify-between">
                <h3 className="font-medium text-sm">{d.title}</h3>
                <span className={`text-xs ${d.confidence >= 0.8 ? 'text-green-400' : d.confidence >= 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>{Math.round(d.confidence * 100)}%</span>
              </div>
              {d.context && <p className="text-xs text-gray-500 mt-1">Context: {d.context}</p>}
              {d.outcome && <p className="text-sm text-gray-300 mt-2">Outcome: {d.outcome}</p>}
              {d.rationale && <p className="text-xs text-gray-500 mt-1">Rationale: {d.rationale}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}