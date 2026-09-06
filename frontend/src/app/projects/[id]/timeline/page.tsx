'use client';
import { useEffect, useState, useCallback } from 'react';
import { TimelineItem, TimelineResponse } from '@/types/api';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { GitBranch, CheckSquare, Brain } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorAlert } from '@/components/ui/ErrorAlert';

export default function TimelinePage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [events, setEvents] = useState<TimelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<TimelineResponse>(`/api/v1/ingest/timeline?project_id=${encodeURIComponent(projectId)}&limit=100`);
      setEvents(data.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load timeline');
    } finally { setLoading(false); }
  }, [user, projectId]);

  useEffect(() => { loadData(); }, [loadData]);

  if (!user) {
    return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to view timeline.</p></div>;
  }

  const typeIcon = (type: string) => {
    if (type === 'decision') return <CheckSquare size={14} className="text-[var(--sv-auth-decision)]" />;
    if (type === 'fact') return <GitBranch size={14} className="text-[var(--sv-evidence-processed)]" />;
    return <Brain size={14} className="text-[var(--sv-evidence-integrated)]" />;
  };

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[var(--sv-text-primary)]">Timeline</h1>
        <p className="text-sm text-[var(--sv-text-tertiary)] mt-1">Chronological view of project knowledge</p>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {loading && <div className="text-sm text-[var(--sv-text-tertiary)]">Loading…</div>}

      {!loading && events.length === 0 && !error && (
        <EmptyState
          icon={<GitBranch size={32} className="text-[var(--sv-text-disabled)]" />}
          title="No events yet"
          description="Timeline events appear as memories, facts, and decisions are extracted."
        />
      )}

      {events.length > 0 && (
        <div className="relative pl-6 border-l border-[var(--sv-border-default)] space-y-4">
          {events.map((ev) => (
            <div key={`${ev.item_type}-${ev.id}`} className="relative">
              <div className="absolute -left-[25px] w-2.5 h-2.5 rounded-full bg-[var(--sv-accent)] border-2 border-[var(--sv-bg-base)]" />
              <p className="text-xs text-[var(--sv-text-disabled)]">{ev.timestamp ? new Date(ev.timestamp).toLocaleString() : 'Unknown date'}</p>
              <div className="flex items-center gap-2 mt-1">
                {typeIcon(ev.item_type)}
                <span className="text-xs text-[var(--sv-text-tertiary)] uppercase font-medium">{ev.item_type}</span>
                {ev.temporal_status && <Badge category="temporal" value={ev.temporal_status.toUpperCase()} size="sm" />}
              </div>
              <p className="text-sm text-[var(--sv-text-secondary)] mt-1.5 leading-relaxed">{ev.title || ev.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
