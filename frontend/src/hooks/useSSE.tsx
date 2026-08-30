'use client';
import { useCallback, useRef } from 'react';
import { ChatStreamEvent } from '@/types/api';

type MessageHandler = (event: ChatStreamEvent) => void;
type DoneHandler = (metadata: { tokens: number; memory_grounded: boolean }) => void;
type ErrorHandler = (detail: string) => void;

export function useSSE() {
  const esRef = useRef<EventSource | null>(null);
  const handlersRef = useRef<{ onMessage: MessageHandler; onDone: DoneHandler; onError: ErrorHandler }>({
    onMessage: () => {}, onDone: () => {}, onError: () => {},
  });

  const stream = useCallback((url: string, onMessage: MessageHandler, onDone: DoneHandler, onError: ErrorHandler) => {
    if (esRef.current) esRef.current.close();
    handlersRef.current = { onMessage, onDone, onError };
    const es = new EventSource(url);
    esRef.current = es;
    es.addEventListener('token', (e: MessageEvent) => handlersRef.current.onMessage(JSON.parse(e.data)));
    es.addEventListener('sources', (e: MessageEvent) => handlersRef.current.onMessage(JSON.parse(e.data)));
    es.addEventListener('done', (e: MessageEvent) => { handlersRef.current.onDone(JSON.parse(e.data).metadata); es.close(); });
    es.addEventListener('error', (e: MessageEvent) => { handlersRef.current.onError(JSON.parse(e.data).detail); es.close(); });
    es.onerror = () => { handlersRef.current.onError('Connection lost'); es.close(); };
    return () => es.close();
  }, []);

  const stop = useCallback(() => { if (esRef.current) { esRef.current.close(); esRef.current = null; } }, []);
  return { stream, stop };
}
