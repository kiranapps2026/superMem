'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { createContext, useContext } from 'react';

type ToastVariant = 'info' | 'success' | 'warning' | 'error';

interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
}

const VARIANT_STYLES: Record<ToastVariant, string> = {
  info:    'border-[var(--sv-info)] bg-[var(--sv-info)]/10',
  success: 'border-[var(--sv-success)] bg-[var(--sv-success)]/10',
  warning: 'border-[var(--sv-warning)] bg-[var(--sv-warning)]/10',
  error:   'border-[var(--sv-error)] bg-[var(--sv-error)]/10',
};

const VARIANT_ICONS: Record<ToastVariant, string> = {
  info:    'ℹ',
  success: '✓',
  warning: '⚠',
  error:   '✕',
};

interface ToastContextValue {
  toast: (message: string, variant?: ToastVariant) => void;
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const remove = useCallback((id: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) { clearTimeout(timer); timersRef.current.delete(id); }
  }, []);

  const toast = useCallback((message: string, variant: ToastVariant = 'info') => {
    const id = crypto.randomUUID();
    setItems((prev) => [...prev, { id, message, variant }]);
    const timer = setTimeout(() => remove(id), 4000);
    timersRef.current.set(id, timer);
    return id;
  }, [remove]);

  // Cleanup timers on unmount
  useEffect(() => () => timersRef.current.forEach((t) => clearTimeout(t)), []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[var(--sv-z-toast)] flex flex-col gap-2 pointer-events-none" role="status" aria-live="polite">
        {items.map((item) => (
          <div
            key={item.id}
            className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg border-l-4 ${VARIANT_STYLES[item.variant]}
              shadow-lg backdrop-blur-sm animate-slide-up max-w-sm`}
            role="alert"
          >
            <span className={`shrink-0 w-5 h-5 flex items-center justify-center rounded-full text-xs font-bold
              ${item.variant === 'error' ? 'bg-[var(--sv-error)] text-white' :
                item.variant === 'success' ? 'bg-[var(--sv-success)] text-white' :
                item.variant === 'warning' ? 'bg-[var(--sv-warning)] text-black' :
                'bg-[var(--sv-info)] text-white'}`}>
              {VARIANT_ICONS[item.variant]}
            </span>
            <p className="text-sm text-[var(--sv-text-primary)] flex-1">{item.message}</p>
            <button
              onClick={() => remove(item.id)}
              className="shrink-0 text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] transition-colors"
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
