'use client';
import { useEffect, useState } from 'react';
import { TimelineEvent } from '@/types/api';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { GitBranch, CheckSquare } from 'lucide-react';

export default function TimelinePage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    apiGet<TimelineEvent[]>(`/api/v1/memory/${projectId}/timeline`).then((e) => { setEvents(e); setLoading(false); }).catch(() => setLoading(false));
  }, [user, projectId]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-6">Timeline</h1>
      {events.length === 0 ? <p className="text-sm text-gray-500">No events yet.</p> : (
        <div className="relative pl-4 border-l border-[var(--border)] space-y-4">
          {events.map((ev) => (
            <div key={ev.id} className="relative">
              <div className="absolute -left-[21px] w-2.5 h-2.5 rounded-full bg-[var(--accent)]" />
              <p className="text-xs text-gray-500">{new Date(ev.timestamp).toLocaleString()}</p>
              <div className="flex items-center gap-2 mt-1">
                {ev.type === 'decision' ? <CheckSquare size={14} className="text-gray-400" /> : <GitBranch size={14} className="text-gray-400" />}
                <span className="text-xs text-gray-400 uppercase">{ev.type}</span>
              </div>
              <p className="text-sm mt-1">{ev.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}