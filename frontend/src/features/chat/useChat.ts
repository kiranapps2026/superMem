'use client';

import { useCallback, useRef, useState } from 'react';
import { ChatStreamEvent } from '@/types/api';
import { useSSE } from '@/hooks/useSSE';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: ChatStreamEvent['sources'];
  metadata?: { tokens: number; memory_grounded: boolean };
  latencyMs?: number;
  model?: string;
  confidence?: number;
}

export function useChat(projectId?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const cancelRef = useRef<(() => void) | null>(null);
  const { stream, stop } = useSSE();

  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim() || streaming) return;
      const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: message };
      setMessages((m) => [...m, userMsg]);
      setLoading(true);
      setError(null);
      setStreaming(true);

      const assistantId = crypto.randomUUID();
      const assistantMsg: ChatMessage = { id: assistantId, role: 'assistant', content: '' };
      setMessages((m) => [...m, assistantMsg]);

      try {
        cancelRef.current = stream(
          message,
          (event: ChatStreamEvent) => {
            if (event.type === 'token' && event.content) {
              setMessages((ms) =>
                ms.map((m) => (m.id === assistantId ? { ...m, content: m.content + event.content } : m))
              );
            } else if (event.type === 'sources' && event.sources) {
              setMessages((ms) =>
                ms.map((m) => (m.id === assistantId ? { ...m, sources: event.sources } : m))
              );
            } else if (event.type === 'error' && event.error) {
              setMessages((ms) =>
                ms.map((m) => (m.id === assistantId ? { ...m, content: `Error: ${event.error}` } : m))
              );
            }
          },
          (metadata) => {
            setMessages((ms) =>
              ms.map((m) => (m.id === assistantId ? { ...m, metadata } : m))
            );
            setStreaming(false);
            setLoading(false);
          },
          (detail) => {
            setError(detail);
            setMessages((ms) =>
              ms.map((m) => (m.id === assistantId ? { ...m, content: `Error: ${detail}` } : m))
            );
            setStreaming(false);
            setLoading(false);
          },
          { projectId: projectId || undefined }
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Chat failed');
        setStreaming(false);
        setLoading(false);
      }
    },
    [stream, projectId]
  );

  const cancelStream = useCallback(() => {
    stop();
    cancelRef.current?.();
    cancelRef.current = null;
    setStreaming(false);
    setLoading(false);
  }, [stop]);

  const clear = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, streaming, error, sendMessage, cancelStream, clear };
}
