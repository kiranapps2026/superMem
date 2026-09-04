'use client';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
}

const SIZE_CLASSES: Record<string, string> = {
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-4 h-8 border-[3px]',
};

export function LoadingSpinner({ size = 'md' }: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={`${SIZE_CLASSES[size]} border-[var(--border)] border-t-[var(--accent)] rounded-full animate-spin`}
    />
  );
}
