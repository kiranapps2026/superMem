'use client';

interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorAlert({ title = 'Error', message, onRetry, onDismiss }: ErrorAlertProps) {
  return (
    <div
      role="alert"
      className="bg-[var(--sv-error)]/10 border border-[var(--sv-error)]/30 rounded-lg p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-medium text-[var(--sv-error)]">{title}</h4>
          <p className="text-sm text-[var(--sv-error)]/80 mt-0.5">{message}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-xs px-2.5 py-1 rounded border border-[var(--sv-error)]/30 text-[var(--sv-error)]/80 hover:bg-[var(--sv-error)]/10 transition-colors"
            >
              Retry
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] transition-colors"
              aria-label="Dismiss error"
            >
              &times;
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
