'use client';

import { ReactNode, useState, useRef, useEffect } from 'react';

interface TooltipProps {
  text: string;
  children: ReactNode;
}

export function Tooltip({ text, children }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const [pos, setPos] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLSpanElement>(null);

  const handleEnter = () => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setPos({
      top: rect.top - 8,
      left: rect.left + rect.width / 2,
    });
    setVisible(true);
  };

  return (
    <span
      ref={triggerRef}
      className="relative inline-flex"
      onMouseEnter={handleEnter}
      onMouseLeave={() => setVisible(false)}
      onFocus={handleEnter}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && (
        <span
          role="tooltip"
          className="fixed z-[var(--sv-z-dropdown)] px-2 py-1 text-xs rounded bg-[var(--sv-bg-overlay)] text-[var(--sv-text-secondary)] border border-[var(--sv-border-default)] shadow-md whitespace-nowrap pointer-events-none"
          style={{ top: `${pos.top}px`, left: `${pos.left}px`, transform: 'translate(-50%, -100%)' }}
        >
          {text}
        </span>
      )}
    </span>
  );
}
