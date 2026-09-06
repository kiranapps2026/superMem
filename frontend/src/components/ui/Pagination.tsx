'use client';

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function Pagination({ page, totalPages, onPageChange, className = '' }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages: (number | string)[] = [];
  pages.push(1);
  if (page > 3) pages.push('…');
  for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
    if (!pages.includes(i)) pages.push(i);
  }
  if (page < totalPages - 2) pages.push('…');
  if (totalPages > 1) pages.push(totalPages);

  return (
    <nav
      role="navigation"
      aria-label="Pagination"
      className={`flex items-center justify-center gap-1 ${className}`}
    >
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
        className="px-2.5 py-1 text-sm rounded-md text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] hover:bg-[var(--sv-bg-overlay)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        aria-label="Previous page"
      >
        &larr;
      </button>
      {pages.map((p, i) =>
        p === '…' ? (
          <span key={`ellipsis-${i}`} className="px-1 text-sm text-[var(--sv-text-disabled)]">…</span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p as number)}
            className={`px-2.5 py-1 text-sm rounded-md transition-colors ${
              page === p
                ? 'bg-[var(--sv-accent)] text-[var(--sv-text-inverse)]'
                : 'text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] hover:bg-[var(--sv-bg-overlay)]'
            }`}
            aria-current={page === p ? 'page' : undefined}
            aria-label={`Page ${p}`}
          >
            {p}
          </button>
        ),
      )}
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages}
        className="px-2.5 py-1 text-sm rounded-md text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] hover:bg-[var(--sv-bg-overlay)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        aria-label="Next page"
      >
        &rarr;
      </button>
    </nav>
  );
}
