'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Project } from '@/types/api';
import { apiGet } from '@/lib/api';
import { FolderOpen } from 'lucide-react';

export default function ProjectsPage() {
  const { user, loading: authLoading } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    apiGet<Project[]>('/api/v1/projects').then((data) => { setProjects(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [user]);

  if (authLoading || loading) return <div className="flex items-center justify-center h-full"><div className="text-sm text-gray-500">Loading…</div></div>;

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-xl font-semibold mb-6">Projects</h1>
      {projects.length === 0 ? (
        <div className="text-center py-20">
          <FolderOpen size={48} className="mx-auto text-gray-600 mb-4" />
          <p className="text-gray-500 text-sm">No projects yet. Create one from the Dashboard.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`}
              className="block bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 hover:border-[var(--accent)]/50 transition-colors">
              <h3 className="font-medium text-sm">{p.name}</h3>
              {p.description && <p className="text-xs text-gray-500 mt-1 line-clamp-2">{p.description}</p>}
              <p className="text-xs text-gray-500 mt-3">{p.session_count} sessions</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
