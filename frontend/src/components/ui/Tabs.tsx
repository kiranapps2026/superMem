'use client';

import { createContext, useContext, useState, useCallback } from 'react';

interface TabsContextValue {
  active: string;
  setActive: (id: string) => void;
}

const TabsContext = createContext<TabsContextValue>({ active: '', setActive: () => {} });

interface TabsProps {
  items: { id: string; label: string }[];
  active: string;
  onSelect: (id: string) => void;
  children: React.ReactNode;
}

export function Tabs({ items, active, onSelect, children }: TabsProps) {
  return (
    <TabsContext.Provider value={{ active, setActive: onSelect }}>
      <div>
        <div role="tablist" className="flex gap-1 border-b border-[var(--sv-border-default)]">
          {items.map((item) => {
            const isActive = active === item.id;
            return (
              <button
                key={item.id}
                role="tab"
                aria-selected={isActive}
                onClick={() => onSelect(item.id)}
                className={`px-3 py-2 text-sm font-medium transition-colors border-b-2 -mb-px
                  ${isActive
                    ? 'border-[var(--sv-accent)] text-[var(--sv-text-primary)]'
                    : 'border-transparent text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-secondary)]'
                  }`}
              >
                {item.label}
              </button>
            );
          })}
        </div>
        <div role="tabpanel" className="mt-4">
          {children}
        </div>
      </div>
    </TabsContext.Provider>
  );
}

interface TabPanelProps {
  value: string;
  children: React.ReactNode;
}

export function TabPanel({ value, children }: TabPanelProps) {
  const { active } = useContext(TabsContext);
  if (active !== value) return null;
  return <>{children}</>;
}
