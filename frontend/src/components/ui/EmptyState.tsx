'use client';

import { type ReactNode } from 'react';

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="text-[var(--sv-text-disabled)] mb-3">{icon}</div>
      <h3 className="text-sm font-medium text-[var(--sv-text-secondary)]">{title}</h3>
      {description && <p className="text-xs text-[var(--sv-text-tertiary)] mt-1 max-w-sm">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
