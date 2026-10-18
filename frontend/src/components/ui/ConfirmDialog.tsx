'use client';

import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  danger = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    document.addEventListener('keydown', handleKey);
    confirmRef.current?.focus();
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center"
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onCancel} />
      <div className="relative bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-lg shadow-xl max-w-sm w-full mx-4 p-5">
        <h3 id="confirm-dialog-title" className="text-sm font-medium text-[var(--sv-text-primary)]">{title}</h3>
        <p className="text-sm text-[var(--sv-text-secondary)] mt-2">{description}</p>
        <div className="flex justify-end gap-2 mt-5">
          <button
            onClick={onCancel}
            className="px-3 py-1.5 text-sm rounded-md text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] hover:bg-[var(--sv-bg-overlay)] border border-[var(--sv-border-default)] transition-colors"
          >
            Cancel
          </button>
          <button
            ref={confirmRef}
            onClick={onConfirm}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              danger
                ? 'bg-[var(--sv-error)] text-[var(--sv-text-inverse)] hover:bg-[var(--sv-error)]/80'
                : 'bg-[var(--sv-accent)] text-[var(--sv-text-inverse)] hover:bg-[var(--sv-accent-hover)]'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
