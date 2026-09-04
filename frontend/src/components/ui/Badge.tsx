'use client';

import { type ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
}

const VARIANTS: Record<string, string> = {
  default: 'bg-gray-500/15 text-gray-300',
  success: 'bg-green-500/15 text-green-300',
  warning: 'bg-yellow-500/15 text-yellow-300',
  danger: 'bg-red-500/15 text-red-300',
  info: 'bg-blue-500/15 text-blue-300',
  purple: 'bg-purple-500/15 text-purple-300',
};

export function Badge({ children, variant = 'default' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full ${VARIANTS[variant]}`}>
      {children}
    </span>
  );
}
