'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { LogOut, FolderOpen, Upload, MessageSquare, GitBranch, Settings, Menu } from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: FolderOpen },
  { href: '/projects', label: 'Projects', icon: FolderOpen },
  { href: '/settings', label: 'Settings & Members', icon: Settings },
];

function ProjectNav({ projectId }: { projectId: string }) {
  const items = [
    { href: `/projects/${projectId}/chat`, label: 'Chat', icon: MessageSquare },
    { href: `/projects/${projectId}/ingest`, label: 'Ingest', icon: Upload },
    { href: `/projects/${projectId}/sessions`, label: 'Sessions', icon: MessageSquare },
    { href: `/projects/${projectId}/memory`, label: 'Memory', icon: GitBranch },
    { href: `/projects/${projectId}/facts`, label: 'Facts', icon: GitBranch },
    { href: `/projects/${projectId}/decisions`, label: 'Decisions', icon: GitBranch },
    { href: `/projects/${projectId}/timeline`, label: 'Timeline', icon: GitBranch },
    { href: `/projects/${projectId}/search`, label: 'Search', icon: GitBranch },
  ];
  return (
    <div className="space-y-0.5">
      {items.map((item) => (
        <Link key={item.href} href={item.href}
          className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
          <item.icon size={14} />{item.label}
        </Link>
      ))}
    </div>
  );
}

export function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const projectMatch = pathname.match(/\/projects\/([^/]+)/);
  const projectId = projectMatch?.[1];

  return (
    <aside className={`${collapsed ? 'w-14' : 'w-56'} border-r border-[var(--border)] bg-[var(--bg-secondary)] flex flex-col transition-all duration-200 shrink-0`}>
      <div className="flex items-center justify-between px-3 h-12 border-b border-[var(--border)]">
        {!collapsed && <Link href="/dashboard" className="text-sm font-semibold tracking-tight">SwarmVault</Link>}
        <button onClick={() => setCollapsed(!collapsed)} className="p-1 rounded hover:bg-white/5 text-gray-400 hover:text-white">
          <Menu size={16} />
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto p-2 space-y-3">
        <div className="space-y-0.5">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link key={item.href} href={item.href}
                className={`flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-colors ${active ? 'bg-[var(--accent)] text-white' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}>
                <item.icon size={14} />{!collapsed && item.label}
              </Link>
            );
          })}
        </div>
        {projectId && !collapsed && (
          <div className="border-t border-[var(--border)] pt-3">
            <p className="px-3 text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wider">Project</p>
            <ProjectNav projectId={projectId} />
          </div>
        )}
      </nav>
      <div className="border-t border-[var(--border)] p-2 space-y-0.5">
        <Link href="/settings"
          className={`flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-colors ${pathname === '/settings' ? 'bg-[var(--accent)] text-white' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}>
          <Settings size={14} />{!collapsed && 'Settings'}
        </Link>
        {user && (
          <button onClick={async () => { await logout(); router.push('/auth/login'); }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-gray-400 hover:text-red-400 hover:bg-red-400/5 transition-colors">
            <LogOut size={14} />{!collapsed && 'Logout'}
          </button>
        )}
      </div>
    </aside>
  );
}
