'use client';

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: { value: number; label: string };
  loading?: boolean;
  className?: string;
}

export function StatCard({ label, value, icon, trend, loading = false, className = '' }: StatCardProps) {
  if (loading) {
    return (
      <div className={`rounded-lg border border-[var(--sv-border-default)] bg-[var(--sv-bg-raised)] p-4 ${className}`}>
        <div className="animate-shimmer h-4 w-20 rounded mb-2" />
        <div className="animate-shimmer h-8 w-16 rounded" />
      </div>
    );
  }

  return (
    <div className={`rounded-lg border border-[var(--sv-border-default)] bg-[var(--sv-bg-raised)] p-4 ${className}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-[var(--sv-text-tertiary)] uppercase tracking-wider">{label}</span>
        {icon && <span className="text-[var(--sv-text-tertiary)]">{icon}</span>}
      </div>
      <div className="mt-2 text-2xl font-semibold text-[var(--sv-text-primary)]">{value}</div>
      {trend && (
        <div className={`mt-1 text-xs ${trend.value >= 0 ? 'text-[var(--sv-success)]' : 'text-[var(--sv-error)]'}`}>
          {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}% <span className="text-[var(--sv-text-tertiary)]">{trend.label}</span>
        </div>
      )}
    </div>
  );
}
