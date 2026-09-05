'use client';

interface ProgressProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md';
  variant?: 'default' | 'success' | 'warning' | 'error';
  label?: string;
}

export function Progress({ value, max = 100, size = 'sm', variant = 'default', label }: ProgressProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  const variantColors: Record<string, string> = {
    default: 'bg-[var(--sv-accent)]',
    success: 'bg-[var(--sv-success)]',
    warning: 'bg-[var(--sv-warning)]',
    error:   'bg-[var(--sv-error)]',
  };

  const height = size === 'sm' ? 'h-1' : 'h-2';

  return (
    <div className="w-full">
      {(label || pct > 0) && (
        <div className="flex justify-between text-xs text-[var(--sv-text-tertiary)] mb-1">
          {label && <span>{label}</span>}
          {pct > 0 && <span>{Math.round(pct)}%</span>}
        </div>
      )}
      <div className={`${height} w-full bg-[var(--sv-bg-sunken)] rounded-full overflow-hidden`}>
        <div
          className={`${height} ${variantColors[variant]} rounded-full transition-all duration-[var(--sv-duration-base)]`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={Math.round(pct)}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}
