'use client';
import { useEffect, useState } from 'react';
import { FactInfo } from '@/types/api';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { GitBranch } from 'lucide-react';

export default function FactsPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [facts, setFacts] = useState<FactInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    apiGet<FactInfo[]>(`/api/v1/memory/${projectId}/facts`).then((f) => { setFacts(f); setLoading(false); }).catch(() => setLoading(false));
  }, [user, projectId]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-1">Facts</h1>
      <p className="text-sm text-gray-500 mb-4">{facts.length} extracted facts</p>
      {facts.length === 0 ? <p className="text-sm text-gray-500">No facts yet.</p> : (
        <div className="space-y-2">
          {facts.map((f) => (
            <div key={f.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3">
              <p className="text-sm">{f.statement}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-gray-500">{f.predicate || f.authority}</span>
                <span className={`text-xs ${f.confidence >= 0.8 ? 'text-green-400' : f.confidence >= 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>{Math.round(f.confidence * 100)}%</span>
                <span className="text-xs text-gray-500">{f.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}