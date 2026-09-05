'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import {
  LayoutDashboard, FolderOpen, LogOut,
  MessageSquare, Upload, Brain, GitBranch,
  ShieldCheck, Clock, Search, Share2, Settings
} from 'lucide-react';
import { useState } from 'react';
import { Tooltip } from '@/components/ui/Tooltip';

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
}

const WORKSPACE_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/projects', label: 'Projects', icon: FolderOpen },
];

const KNOWLEDGE_ITEMS: NavItem[] = [
  { href: '/search', label: 'Knowledge Search', icon: Search },
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/memory', label: 'Memory', icon: Brain },
  { href: '/facts', label: 'Facts', icon: ShieldCheck },
  { href: '/decisions', label: 'Decisions', icon: ShieldCheck },
  { href: '/timeline', label: 'Timeline', icon: Clock },
  { href: '/graph', label: 'Graph', icon: Share2 },
  { href: '/provenance', label: 'Provenance', icon: GitBranch },
];

const INGESTION_ITEMS: NavItem[] = [
  { href: '/ingest', label: 'Upload & Ingest', icon: Upload },
];

const ACCOUNT_ITEMS: NavItem[] = [
  { href: '/settings', label: 'Settings', icon: Settings },
];

function ProjectNav({ projectId }: { projectId: string }) {
  const items: NavItem[] = [
    { href: `/projects/${projectId}/chat`, label: 'Chat', icon: MessageSquare },
    { href: `/projects/${projectId}/ingest`, label: 'Ingest', icon: Upload },
    { href: `/projects/${projectId}/sessions`, label: 'Sessions', icon: Clock },
    { href: `/projects/${projectId}/memory`, label: 'Memory', icon: Brain },
    { href: `/projects/${projectId}/facts`, label: 'Facts', icon: ShieldCheck },
    { href: `/projects/${projectId}/decisions`, label: 'Decisions', icon: ShieldCheck },
    { href: `/projects/${projectId}/timeline`, label: 'Timeline', icon: Clock },
    { href: `/projects/${projectId}/search`, label: 'Search', icon: Search },
    { href: `/projects/${projectId}/graph`, label: 'Graph', icon: Share2 },
    { href: `/projects/${projectId}/provenance`, label: 'Provenance', icon: GitBranch },
  ];

  return (
    <div className="space-y-0.5">
      {items.map((item) => (
        <NavLink key={item.href} item={item} />
      ))}
    </div>
  );
}

function NavLink({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const active = pathname === item.href || pathname.startsWith(item.href + '/');

  return (
    <Link
      href={item.href}
      className={`flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-colors
        ${active
          ? 'bg-[var(--sv-accent)] text-white'
          : 'text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] hover:bg-white/5'
        }`}
    >
      <item.icon size={14} />
      <span>{item.label}</span>
    </Link>
  );
}

function NavGroup({ label, items }: { label: string; items: NavItem[] }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="space-y-0.5">
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="w-full px-3 py-1 text-xs font-semibold text-[var(--sv-text-tertiary)] uppercase tracking-wider hover:text-[var(--sv-text-secondary)] transition-colors flex items-center gap-1"
        aria-expanded={!collapsed}
      >
        <span className={`transition-transform duration-[var(--sv-duration-base)] ${collapsed ? '' : 'rotate-90'}`} aria-hidden="true">▸</span>
        {label}
      </button>
      {!collapsed && items.map((item) => (
        <NavLink key={item.href} item={item} />
      ))}
    </div>
  );
}

export function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const projectMatch = pathname.match(/\/projects\/([^/]+)/);
  const projectId = projectMatch?.[1];

  return (
    <aside className={`${sidebarCollapsed ? 'w-14' : 'w-56'} border-r border-[var(--sv-border-default)] bg-[var(--sv-bg-raised)] flex flex-col transition-all duration-[var(--sv-duration-base)] shrink-0`}>
      {/* Brand */}
      <div className="flex items-center justify-between px-3 h-12 border-b border-[var(--sv-border-default)]">
        {!sidebarCollapsed && (
          <Link href="/dashboard" className="text-sm font-semibold tracking-tight text-[var(--sv-text-primary)]">
            SwarmVault
          </Link>
        )}
        <Tooltip text={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
          <button
            onClick={() => setSidebarCollapsed((c) => !c)}
            className="p-1.5 rounded-md hover:bg-white/5 text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] transition-colors"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              {sidebarCollapsed ? (
                <path d="M6 3l5 5-5 5" />
              ) : (
                <path d="M10 3l-5 5 5 5" />
              )}
            </svg>
          </button>
        </Tooltip>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-4" aria-label="Main">
        <NavGroup label="Workspace" items={WORKSPACE_ITEMS} />
        <NavGroup label="Knowledge" items={KNOWLEDGE_ITEMS} />
        <NavGroup label="Ingestion" items={INGESTION_ITEMS} />

        {projectId && !sidebarCollapsed && (
          <div className="border-t border-[var(--sv-border-subtle)] pt-3">
            <p className="px-3 text-xs font-semibold text-[var(--sv-text-tertiary)] uppercase tracking-wider mb-1.5">Project</p>
            <ProjectNav projectId={projectId} />
          </div>
        )}
      </nav>

      {/* Bottom: Account */}
      <div className="border-t border-[var(--sv-border-default)] p-2 space-y-0.5">
        <NavGroup label="Account" items={ACCOUNT_ITEMS} />
        <Tooltip text="Logout">
          <button
            onClick={async () => { await logout(); router.push('/auth/login'); }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-[var(--sv-text-tertiary)] hover:text-[var(--sv-error)] hover:bg-[var(--sv-error)]/5 transition-colors"
            aria-label="Logout"
          >
            <LogOut size={14} />
            {!sidebarCollapsed && <span>Logout</span>}
          </button>
        </Tooltip>
      </div>
    </aside>
  );
}
