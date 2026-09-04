'use client';

import { useCallback, useRef, useState } from 'react';
import { ChatRequest, ChatResponse } from '@/types/api';
import { streamChat } from '@/lib/api';
import { useSSE } from '@/hooks/useSSE';
import { ChatStreamEvent } from '@/types/api';

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

  const sendMessage = useCallback(async (message: string) => {
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
      const abortController = new AbortController();
      const url = `/api/v1/chat/stream?project_id=${encodeURIComponent(projectId || '')}`;
      const cleanup = stream(url,
        (event: ChatStreamEvent) => {
          if (event.type === 'token' && event.content) {
            setMessages((ms) =>
              ms.map((m) => m.id === assistantId ? { ...m, content: m.content + event.content } : m)
            );
          } else if (event.type === 'done' && event.metadata) {
            setMessages((ms) =>
              ms.map((m) => m.id === assistantId ? { ...m, metadata: event.metadata } : m)
            );
          } else if (event.type === 'error') {
            setMessages((ms) =>
              ms.map((m) => m.id === assistantId ? { ...m, content: `Error: ${event.error || 'Unknown'}` } : m)
            );
          }
        },
        (metadata) => {
          setMessages((ms) =>
            ms.map((m) => m.id === assistantId ? { ...m, metadata } : m)
          );
          setStreaming(false);
          setLoading(false);
        },
        (detail) => {
          setError(detail);
          setMessages((ms) =>
            ms.map((m) => m.id === assistantId ? { ...m, content: `Error: ${detail}` } : m)
          );
          setStreaming(false);
          setLoading(false);
        }
      );
      cancelRef.current = cleanup;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Chat failed');
      setStreaming(false);
      setLoading(false);
    }
  }, [projectId, streaming, stream]);

  const cancelStream = useCallback(() => {
    stop();
    cancelRef.current?.();
    cancelRef.current = null;
    setStreaming(false);
    setLoading(false);
  }, [stop]);

  const clear = useCallback(() => { setMessages([]); setError(null); }, []);

  return { messages, loading, streaming, error, sendMessage, cancelStream, clear };
}
