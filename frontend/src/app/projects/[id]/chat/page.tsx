'use client';
import { useEffect, useState, useRef, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter, useParams } from 'next/navigation';
import { apiPost, getToken, streamChat } from '@/lib/api';
import {
  MessageSquare, Send, User, Bot, Loader2, ArrowLeft, Sparkles,
  FileText, X, AlertCircle, RefreshCw, ChevronRight
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  usage?: { prompt_tokens: number; completion_tokens: number };
  isStreaming?: boolean;
  sources?: { memory_id: string; content: string; memory_type: string; score: number }[];
}

export default function ChatPage() {
  const { user } = useAuth();
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [evidenceModal, setEvidenceModal] = useState<{ sources: ChatMessage['sources']; content: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMsg: ChatMessage = { role: 'user', content: input.trim() };
    const assistantPlaceholder: ChatMessage = { role: 'assistant', content: '', isStreaming: true };

    setMessages((m) => [...m, userMsg, assistantPlaceholder]);
    setInput('');
    setLoading(true);
    setShowSources(false);
    setError(null);
    abortRef.current = new AbortController();

    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    try {
      const token = getToken();
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      // Create session first
      const sessionRes = await fetch(`${API_BASE}/api/v1/sessions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify({ project_id: projectId }),
      });

      let sessionId: string | null = null;
      if (sessionRes.ok) {
        const sessionData = await sessionRes.json();
        sessionId = sessionData.id;
      }

      // Stream response
      const res = await fetch(`${API_BASE}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify({ message: userMsg.content, session_id: sessionId, project_id: projectId }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        const text = await res.text();
        let detail = text;
        try { const j = JSON.parse(text); detail = j.detail || text; } catch {}
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { role: 'assistant', content: `Error: ${detail}` };
          return copy;
        });
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { role: 'assistant', content: 'Error: no response body' };
          return copy;
        });
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';
      let currentSources: { memory_id: string; content: string; memory_type: string; score: number }[] = [];
      let finalMeta: { model?: string; usage?: { prompt_tokens: number; completion_tokens: number }; latency_ms?: number } = {};

      while (true) {
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
            const event = JSON.parse(payload) as Record<string, unknown>;
            switch (event.type) {
              case 'token':
                fullContent += (event.content as string) || '';
                setMessages((m) => {
                  const copy = [...m];
                  copy[copy.length - 1] = { role: 'assistant', content: fullContent, isStreaming: true };
                  return copy;
                });
                break;
              case 'sources':
                currentSources = (event.sources as typeof currentSources) || [];
                setMessages((m) => {
                  const copy = [...m];
                  copy[copy.length - 1] = { ...copy[copy.length - 1], sources: currentSources };
                  return copy;
                });
                if (currentSources.length > 0) setShowSources(true);
                break;
              case 'done':
                finalMeta = {
                  model: event.model as string | undefined,
                  usage: event.usage as { prompt_tokens: number; completion_tokens: number } | undefined,
                  latency_ms: event.latency_ms as number | undefined,
                };
                setMessages((m) => {
                  const copy = [...m];
                  copy[copy.length - 1] = {
                    role: 'assistant',
                    content: fullContent,
                    sources: currentSources,
                    model: finalMeta.model || 'mock',
                    usage: finalMeta.usage || { prompt_tokens: 0, completion_tokens: 0 },
                    isStreaming: false,
                  };
                  return copy;
                });
                break;
              case 'error':
                setMessages((m) => {
                  const copy = [...m];
                  copy[copy.length - 1] = { role: 'assistant', content: `Error: ${(event.detail as string) || 'Unknown'}` };
                  return copy;
                });
                break;
            }
          } catch {}
        }
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { role: 'assistant', content: 'Stream aborted.', isStreaming: false };
          return copy;
        });
        return;
      }
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { role: 'assistant', content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}` };
        return copy;
      });
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }, [input, loading, projectId]);

  const handleRetry = useCallback(() => {
    if (messages.length > 0 && messages[messages.length - 1].role === 'user') {
      // If the last message is a user message with no response, retry sending
      const lastUserMsg = messages[messages.length - 1].content;
      setInput(lastUserMsg);
      setRetrying(true);
      setError(null);
    }
  }, [messages]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  if (!user) {
    return <div className="flex items-center justify-center h-full"><p className="text-sm text-[var(--sv-text-tertiary)]">Sign in to chat.</p></div>;
  }

  const lastMsg = messages[messages.length - 1];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--sv-border-default)] flex items-center gap-3 shrink-0">
        <button onClick={() => router.back()} className="p-1 rounded hover:bg-[var(--sv-accent-subtle)] text-[var(--sv-text-tertiary)] hover:text-[var(--sv-text-primary)] transition-colors">
          <ArrowLeft size={16} />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-[var(--sv-accent)]" />
            <h1 className="font-semibold text-sm text-[var(--sv-text-primary)]">AI Chat</h1>
            <ChevronRight size={14} className="text-[var(--sv-text-disabled)]" />
            <Badge variant="muted" size="sm">Project</Badge>
          </div>
          <p className="text-xs text-[var(--sv-text-tertiary)] mt-0.5">Grounded in project memory</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="animate-slide-up">
            <EmptyState
              icon={<Sparkles size={32} className="text-[var(--sv-accent)]" />}
              title="Start a conversation"
              description="Ask anything about this project's memory and ingested data."
            />
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${m.role === 'user' ? 'bg-[var(--sv-accent)]' : 'bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)]'}`}>
              {m.role === 'user' ? <User size={14} className="text-white" /> : <Bot size={14} className="text-[var(--sv-text-tertiary)]" />}
            </div>
            <div className={`max-w-[70%] px-3.5 py-2.5 rounded-xl text-sm whitespace-pre-wrap leading-relaxed ${m.role === 'user' ? 'bg-[var(--sv-accent)] text-[var(--sv-text-inverse)] rounded-tr-sm' : 'bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-tl-sm text-[var(--sv-text-primary)]'}`}>
              {m.isStreaming && !m.content ? (
                <span className="flex items-center gap-2 text-[var(--sv-text-tertiary)]">
                  <Loader2 size={14} className="animate-spin" /> Thinking…
                </span>
              ) : m.content}
              {m.isStreaming && m.content && (
                <span className="inline-block w-1.5 h-4 bg-[var(--sv-accent)] ml-0.5 align-middle" />
              )}
              {m.role === 'assistant' && !m.isStreaming && m.sources && m.sources.length > 0 && (
                <button onClick={() => setEvidenceModal({ sources: m.sources!, content: m.content })}
                  className="flex items-center gap-1 text-xs text-[var(--sv-accent)] hover:text-[var(--sv-accent-hover)] mt-2 pt-2 border-t border-[var(--sv-border-default)] transition-colors">
                  <FileText size={12} /> Why this answer?
                </button>
              )}
              {m.role === 'assistant' && !m.isStreaming && !m.content && (
                <span className="text-[var(--sv-error)] text-xs">(empty response)</span>
              )}
            </div>
          </div>
        ))}
        {error && (
          <div className="animate-slide-up">
            <ErrorAlert message={error} onDismiss={() => setError(null)} />
          </div>
        )}
        {retrying && (
          <div className="flex items-center gap-2 text-xs text-[var(--sv-text-tertiary)]">
            <RefreshCw size={12} className="animate-spin" /> Retrying…
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Sources panel */}
      {showSources && messages.some((m) => m.role === 'assistant' && m.sources && m.sources.length > 0) && (
        <div className="px-4 py-2 border-t border-[var(--sv-border-default)] bg-[var(--sv-bg-overlay)]/50 max-h-40 overflow-y-auto animate-slide-up">
          <div className="flex items-center gap-2 mb-1.5">
            <FileText size={12} className="text-[var(--sv-text-tertiary)]" />
            <span className="text-xs text-[var(--sv-text-tertiary)] font-medium">Evidence sources</span>
          </div>
          {messages.filter(m => m.role === 'assistant' && m.sources && m.sources.length > 0).at(-1)?.sources?.map((s, idx) => (
            <div key={idx} className="text-xs text-[var(--sv-text-secondary)] bg-[var(--sv-bg-raised)] rounded px-2 py-1.5 mb-1 border border-[var(--sv-border-subtle)]">
              <span className="text-[var(--sv-accent)]">[{s.memory_type}]</span> {s.content}
              <span className="text-[var(--sv-text-disabled)] ml-2">Score: {Math.round(s.score * 100)}%</span>
            </div>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="border-t border-[var(--sv-border-default)] p-3 shrink-0">
        <div className="flex gap-2 items-end max-w-4xl mx-auto">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => { setInput(e.target.value); e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'; }}
            onKeyDown={handleKeyDown}
            placeholder="Ask about this project…"
            rows={1}
            disabled={loading}
            className="flex-1 bg-[var(--sv-bg-input)] border border-[var(--sv-border-default)] rounded-lg px-3.5 py-2.5 text-sm text-[var(--sv-text-primary)] placeholder:text-[var(--sv-text-disabled)] resize-none focus:outline-none focus:border-[var(--sv-accent)] disabled:opacity-50 max-h-48 transition-colors"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="shrink-0 bg-[var(--sv-accent)] hover:bg-[var(--sv-accent-hover)] text-[var(--sv-text-inverse)] p-2.5 rounded-lg disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
        <p className="text-xs text-[var(--sv-text-disabled)] mt-1.5 text-center">Press Enter to send, Shift+Enter for new line</p>
      </div>

      {/* Evidence Modal */}
      {evidenceModal && (
        <div className="fixed inset-0 bg-black/60 z-[var(--sv-z-modal)] flex items-center justify-center p-4" onClick={() => setEvidenceModal(null)}>
          <div className="bg-[var(--sv-bg-raised)] border border-[var(--sv-border-default)] rounded-xl max-w-lg w-full max-h-[80vh] overflow-y-auto animate-slide-up" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-[var(--sv-border-default)]">
              <h3 className="font-medium text-sm text-[var(--sv-text-primary)]">Why this answer?</h3>
              <button onClick={() => setEvidenceModal(null)} className="p-1 rounded hover:bg-[var(--sv-accent-subtle)] text-[var(--sv-text-tertiary)] transition-colors"><X size={16} /></button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <p className="text-xs text-[var(--sv-text-tertiary)] uppercase tracking-wider mb-2">Answer</p>
                <p className="text-sm text-[var(--sv-text-secondary)] bg-[var(--sv-bg-input)] rounded-lg p-3">{evidenceModal.content}</p>
              </div>
              {(() => {
                const srcs = evidenceModal.sources || [];
                if (srcs.length === 0) return <p className="text-xs text-[var(--sv-text-tertiary)]">This answer was generated from general knowledge without specific memory retrieval.</p>;
                return (
                  <div>
                    <p className="text-xs text-[var(--sv-text-tertiary)] uppercase tracking-wider mb-2">Evidence trail</p>
                    <div className="space-y-2">
                      {srcs.map((s, i) => (
                        <div key={i} className="bg-[var(--sv-bg-input)] rounded-lg p-3 space-y-1 border border-[var(--sv-border-subtle)]">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-medium bg-[var(--sv-accent)]/20 text-[var(--sv-accent)] px-2 py-0.5 rounded">{s.memory_type}</span>
                            <span className="text-xs text-[var(--sv-text-tertiary)]">Score: {Math.round(s.score * 100)}%</span>
                          </div>
                          <p className="text-sm text-[var(--sv-text-secondary)]">{s.content}</p>
                          <div className="flex items-center gap-1 text-xs text-[var(--sv-text-disabled)]">
                            <span className="font-mono">{s.memory_id.slice(0, 8)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-[var(--sv-text-disabled)] mt-3">
                      Each source links back to a memory extracted from an ingested conversation.
                    </p>
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
