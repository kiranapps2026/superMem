'use client';

import { type ReactNode, useState, useCallback, useRef } from 'react';

interface FileInputProps {
  onFile: (file: File) => void;
  accept?: string;
  disabled?: boolean;
  children?: ReactNode;
}

export function FileInput({ onFile, accept, disabled, children }: FileInputProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    if (!disabled) onFile(file);
  }, [onFile, disabled]);

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click(); }}
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        if (!disabled && e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
      }}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        dragOver
          ? 'border-[var(--accent)] bg-[var(--accent)]/5'
          : 'border-[var(--border)] hover:border-gray-600'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        disabled={disabled}
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        className="hidden"
        aria-label="File upload"
      />
      {children || (
        <div>
          <p className="text-sm text-gray-400">Drop a file here or click to browse</p>
          {accept && <p className="text-xs text-gray-600 mt-1">{accept}</p>}
        </div>
      )}
    </div>
  );
}
