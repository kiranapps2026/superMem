'use client';

import { useCallback, useRef } from 'react';
import { getToken } from '@/lib/api';
import { ChatStreamEvent } from '@/types/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type MessageHandler = (event: ChatStreamEvent) => void;
type DoneHandler = (metadata: { tokens: number; memory_grounded: boolean }) => void;
type ErrorHandler = (detail: string) => void;

interface StreamOptions {
  projectId?: string;
  sessionId?: string;
}

export function useSSE() {
  const controllerRef = useRef<AbortController | null>(null);

  const stream = useCallback(
    (message: string, onMessage: MessageHandler, onDone: DoneHandler, onError: ErrorHandler, opts?: StreamOptions) => {
      if (controllerRef.current) {
        controllerRef.current.abort();
      }

      const controller = new AbortController();
      controllerRef.current = controller;

      const run = async () => {
        try {
          const token = getToken();
          const body: Record<string, unknown> = { message };
          if (opts?.projectId) body.project_id = opts.projectId;
          if (opts?.sessionId) body.session_id = opts.sessionId;

          const res = await fetch(`${API_BASE}/api/v1/chat/stream`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify(body),
            signal: controller.signal,
          });

          if (!res.ok) {
            const text = await res.text();
            let detail = text;
            try {
              const j = JSON.parse(text);
              detail = j.detail || j.message || text;
            } catch {}
            throw new Error(detail || `HTTP ${res.status}`);
          }

          const reader = res.body?.getReader();
          if (!reader) throw new Error('No response body');

          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
            if (controller.signal.aborted) {
              reader.cancel();
              return;
            }

            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed.startsWith('data: ')) continue;
              const payload = trimmed.slice(6).trim();
              if (!payload) continue;

              try {
                const event = JSON.parse(payload) as ChatStreamEvent;
                switch (event.type) {
                  case 'token':
                    if (event.content) onMessage(event);
                    break;
                  case 'sources':
                    onMessage({ type: 'sources', content: '', sources: event.sources });
                    break;
                  case 'done':
                    onDone(event.metadata || { tokens: 0, memory_grounded: false });
                    return;
                  case 'error':
                    onError(event.error || 'Stream error');
                    return;
                }
              } catch {
                // skip malformed event payload
              }
            }
          }

          // Stream ended without explicit done event — finalize
          onDone({ tokens: 0, memory_grounded: false });
        } catch (err) {
          if (err instanceof Error && err.message === 'Stream cancelled') return;
          onError(err instanceof Error ? err.message : 'Connection lost');
        }
      };

      run();

      return () => {
        controller.abort();
      };
    },
    []
  );

  const stop = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
  }, []);

  return { stream, stop };
}
