'use client';

import { type ReactNode } from 'react';

/* ── Variant categories ───────────────────────────────── */

const STATUS_VARIANTS: Record<string, string> = {
  default:  'bg-gray-500/15 text-gray-300',
  success:  'bg-[var(--sv-success)]/15 text-[var(--sv-success)]',
  warning:  'bg-[var(--sv-warning)]/15 text-[var(--sv-warning)]',
  danger:   'bg-[var(--sv-error)]/15 text-[var(--sv-error)]',
  info:     'bg-[var(--sv-info)]/15 text-[var(--sv-info)]',
  purple:   'bg-[var(--sv-auth-decision)]/15 text-[var(--sv-auth-decision)]',
};

const AUTHORITY_VARIANTS: Record<string, string> = {
  UNVERIFIED: 'bg-gray-500/15 text-gray-300',
  INFERRED:   'bg-[var(--sv-auth-inferred)]/15 text-[var(--sv-auth-inferred)]',
  OBSERVED:   'bg-[var(--sv-auth-observed)]/15 text-[var(--sv-auth-observed)]',
  DECISION:   'bg-[var(--sv-auth-decision)]/15 text-[var(--sv-auth-decision)]',
  VERIFIED:   'bg-[var(--sv-auth-verified)]/15 text-[var(--sv-auth-verified)]',
  CERTIFIED:  'bg-[var(--sv-auth-certified)]/15 text-[var(--sv-auth-certified)]',
};

const EVIDENCE_VARIANTS: Record<string, string> = {
  INGESTED:   'bg-gray-500/15 text-gray-300',
  PROCESSED:  'bg-[var(--sv-evidence-processed)]/15 text-[var(--sv-evidence-processed)]',
  INTEGRATED: 'bg-[var(--sv-evidence-integrated)]/15 text-[var(--sv-evidence-integrated)]',
  PROVEN:     'bg-[var(--sv-evidence-proven)]/15 text-[var(--sv-evidence-proven)]',
};

const TEMPORAL_VARIANTS: Record<string, string> = {
  ACTIVE:     'bg-[var(--sv-temporal-active)]/15 text-[var(--sv-temporal-active)]',
  SUPERSEDED: 'bg-[var(--sv-temporal-superseded)]/15 text-[var(--sv-temporal-superseded)]',
  ARCHIVED:   'bg-[var(--sv-temporal-archived)]/15 text-[var(--sv-temporal-archived)]',
};

type BadgeCategory = 'status' | 'authority' | 'evidence' | 'temporal';

interface BadgeProps {
  children?: ReactNode;
  category?: BadgeCategory;
  value?: string;
  variant?: string;
  size?: 'sm' | 'md';
  className?: string;
}

export function Badge({ children, category, value, variant, size = 'md', className = '' }: BadgeProps) {
  const sizeClasses = size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5';
  let classes = `inline-flex items-center font-medium rounded-full ${sizeClasses}`;

  // New API: category + value
  if (category === 'authority' && value) {
    classes += ` ${AUTHORITY_VARIANTS[value] || AUTHORITY_VARIANTS.UNVERIFIED}`;
  } else if (category === 'evidence' && value) {
    classes += ` ${EVIDENCE_VARIANTS[value] || EVIDENCE_VARIANTS.INGESTED}`;
  } else if (category === 'temporal' && value) {
    classes += ` ${TEMPORAL_VARIANTS[value] || TEMPORAL_VARIANTS.ACTIVE}`;
  }
  // Legacy API: variant (status variant)
  else if (variant) {
    classes += ` ${STATUS_VARIANTS[variant] || STATUS_VARIANTS.default}`;
  }
  // Auto-detect from children string (e.g. "current", "failed")
  else if (typeof children === 'string') {
    classes += ` ${STATUS_VARIANTS[children.toLowerCase()] || STATUS_VARIANTS.default}`;
  }
  else {
    classes += ` ${STATUS_VARIANTS.default}`;
  }

  return (
    <span className={`${classes} ${className}`}>
      {(category && value) ? value.toLowerCase() : children}
    </span>
  );
}
