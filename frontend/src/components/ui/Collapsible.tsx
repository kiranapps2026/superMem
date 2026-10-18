'use client';

import { useState, useCallback, useEffect, useRef } from 'react';

interface CollapsibleProps {
  label: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  badge?: React.ReactNode;
}

export function Collapsible({ label, children, defaultOpen = false, badge }: CollapsibleProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border border-[var(--sv-border-default)] rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-[var(--sv-text-primary)] bg-[var(--sv-bg-raised)] hover:bg-[var(--sv-bg-overlay)] transition-colors"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2">
          <span className={`transition-transform duration-[var(--sv-duration-base)] ${open ? 'rotate-90' : ''}`} aria-hidden="true">▸</span>
          {label}
          {badge}
        </span>
      </button>
      <div
        className={`overflow-hidden transition-all duration-[var(--sv-duration-base)] ${open ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}`}
        aria-hidden={!open}
      >
        <div className="px-4 py-3 text-sm text-[var(--sv-text-secondary)] bg-[var(--sv-bg-base)]">
          {children}
        </div>
      </div>
    </div>
  );
}
