'use client';

import { type ReactNode } from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
}

export function Card({ title, subtitle, children, className = '', actions }: CardProps) {
  return (
    <div className={`bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
          <div>
            {title && <h3 className="text-sm font-medium">{title}</h3>}
            {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}
