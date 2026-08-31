'use client';
import { useEffect, useState, useCallback } from 'react';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { GitBranch, CheckSquare } from 'lucide-react';

interface TimelineEvent {
  item_type: 'memory' | 'fact' | 'decision';
  id: string;
  title: string;
  timestamp: string | null;
  temporal_status: string | null;
  content: string;
}

export default function TimelinePage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!user) return;
    try {
      const data = await apiGet<{ items: TimelineEvent[] }>(`/api/v1/ingest/timeline?project_id=${encodeURIComponent(projectId)}&limit=100`);
      setEvents(data.items || []);
    } catch {}
    finally { setLoading(false); }
  }, [user, projectId]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-6">Timeline</h1>
      {events.length === 0 ? <p className="text-sm text-gray-500">No events yet.</p> : (
        <div className="relative pl-4 border-l border-[var(--border)] space-y-4">
          {events.map((ev) => (
            <div key={`${ev.item_type}-${ev.id}`} className="relative">
              <div className="absolute -left-[21px] w-2.5 h-2.5 rounded-full bg-[var(--accent)]" />
              <p className="text-xs text-gray-500">{ev.timestamp ? new Date(ev.timestamp).toLocaleString() : 'Unknown date'}</p>
              <div className="flex items-center gap-2 mt-1">
                {ev.item_type === 'decision' ? <CheckSquare size={14} className="text-gray-400" /> : <GitBranch size={14} className="text-gray-400" />}
                <span className="text-xs text-gray-400 uppercase">{ev.item_type}</span>
                {ev.temporal_status && (
                  <span className={`text-xs px-2 py-0.5 rounded ${ev.temporal_status === 'current' ? 'bg-green-400/10 text-green-400' : 'bg-yellow-400/10 text-yellow-400'}`}>{ev.temporal_status}</span>
                )}
              </div>
              <p className="text-sm mt-1 line-clamp-3">{ev.title || ev.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
