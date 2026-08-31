'use client';
import { useEffect, useState, useCallback } from 'react';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { GitBranch } from 'lucide-react';

interface FactItem {
  id: string;
  statement: string;
  predicate: string | null;
  authority: string;
  confidence: number;
  status: string;
  created_at: string;
}

export default function FactsPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [facts, setFacts] = useState<FactItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!user) return;
    try {
      const data = await apiGet<{ items: FactItem[] }>(`/api/v1/ingest/facts?project_id=${encodeURIComponent(projectId)}`);
      setFacts(data.items || []);
    } catch {}
    finally { setLoading(false); }
  }, [user, projectId]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-1">Facts</h1>
      <p className="text-sm text-gray-500 mb-4">{facts.length} extracted facts</p>
      {facts.length === 0 ? <p className="text-sm text-gray-500">No facts yet. Ingest conversations to extract knowledge.</p> : (
        <div className="space-y-2">
          {facts.map((f) => (
            <div key={f.id} className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-3">
              <p className="text-sm">{f.statement}</p>
              <div className="flex items-center gap-2 mt-2">
                {f.predicate && <span className="text-xs text-gray-500">{f.predicate}</span>}
                <span className={`text-xs ${f.confidence >= 0.8 ? 'text-green-400' : f.confidence >= 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>{Math.round(f.confidence * 100)}%</span>
                <span className="text-xs text-gray-500">{f.status}</span>
                <span className="text-xs text-gray-500">{f.authority}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
