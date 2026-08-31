'use client';
import { useEffect, useState, useRef, useCallback } from 'react';
import { apiGet, getToken } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { MessageSquare, Send, User, Bot, Loader2, ArrowLeft, Sparkles, FileText, X } from 'lucide-react';

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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [evidenceModal, setEvidenceModal] = useState<{ sources: ChatMessage['sources']; content: string } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMsg: ChatMessage = { role: 'user', content: input.trim() };
    const assistantPlaceholder: ChatMessage = { role: 'assistant', content: '', isStreaming: true };

    setMessages((m) => [...m, userMsg, assistantPlaceholder]);
    setInput('');
    setLoading(true);
    setShowSources(false);

    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const token = getToken();

      const res = await fetch(`${API_BASE}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify({ message: userMsg.content }),
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
                setMessages((m) => {
                  const copy = [...m];
                  copy[copy.length - 1] = {
                    role: 'assistant',
                    content: fullContent,
                    sources: currentSources,
                    model: (event.model as string) || 'mock',
                    usage: (event.usage as { prompt_tokens: number; completion_tokens: number }) || { prompt_tokens: 0, completion_tokens: 0 },
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
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { role: 'assistant', content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}` };
        return copy;
      });
    } finally {
      setLoading(false);
    }
  }, [input, loading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  if (!user) {
    return <div className="flex items-center justify-center h-full"><p className="text-sm text-gray-500">Sign in to chat.</p></div>;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--border)] flex items-center gap-3 shrink-0">
        <button onClick={() => router.back()} className="p-1 rounded hover:bg-white/5 text-gray-400 hover:text-white">
          <ArrowLeft size={16} />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-[var(--accent)]" />
            <h1 className="font-semibold text-sm">AI Chat</h1>
          </div>
          <p className="text-xs text-gray-500">Grounded in project memory</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-20">
            <div className="w-12 h-12 rounded-full bg-[var(--accent)]/10 flex items-center justify-center mx-auto mb-4">
              <Sparkles size={24} className="text-[var(--accent)]" />
            </div>
            <p className="text-gray-400 text-sm font-medium">Start a conversation</p>
            <p className="text-gray-500 text-xs mt-1">Ask anything about this project&#39;s memory and ingested data.</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${m.role === 'user' ? 'bg-[var(--accent)]' : 'bg-[var(--bg-tertiary)] border border-[var(--border)]'}`}>
              {m.role === 'user' ? <User size={14} className="text-white" /> : <Bot size={14} className="text-gray-400" />}
            </div>
            <div className={`max-w-[70%] px-3.5 py-2.5 rounded-xl text-sm whitespace-pre-wrap leading-relaxed ${m.role === 'user' ? 'bg-[var(--accent)] text-white rounded-tr-sm' : 'bg-[var(--bg-secondary)] border border-[var(--border)] rounded-tl-sm'}`}>
              {m.isStreaming && !m.content ? (
                <span className="flex items-center gap-2 text-gray-500">
                  <Loader2 size={14} className="animate-spin" /> Thinking&hellip;
                </span>
              ) : m.content}
              {m.isStreaming && m.content && (
                <span className="inline-block w-1.5 h-4 bg-[var(--accent)] ml-0.5 align-middle animate-pulse-dot" />
              )}
              {m.role === 'assistant' && !m.isStreaming && m.sources && m.sources.length > 0 && (
                <button onClick={() => setEvidenceModal({ sources: m.sources!, content: m.content })}
                  className="flex items-center gap-1 text-xs text-[var(--accent)] hover:text-[var(--accent-hover)] mt-2 pt-2 border-t border-[var(--border)]">
                  <FileText size={12} /> Why this answer?
                </button>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Sources panel */}
      {showSources && messages.some((m) => m.role === 'assistant' && m.sources && m.sources.length > 0) && (
        <div className="px-4 py-2 border-t border-[var(--border)] bg-[var(--bg-secondary)]/50 max-h-40 overflow-y-auto">
          <div className="flex items-center gap-2 mb-1.5">
            <FileText size={12} className="text-gray-500" />
            <span className="text-xs text-gray-500 font-medium">Evidence sources</span>
          </div>
          {messages.filter(m => m.role === 'assistant' && m.sources && m.sources.length > 0).at(-1)?.sources?.map((s, idx) => (
            <div key={idx} className="text-xs text-gray-400 bg-[var(--bg-tertiary)] rounded px-2 py-1.5 mb-1 line-clamp-2">
              <span className="text-[var(--accent)]">[{s.memory_type}]</span> {s.content}
              <span className="text-gray-600 ml-2">Score: {Math.round(s.score * 100)}%</span>
            </div>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="border-t border-[var(--border)] p-3 shrink-0">
        <div className="flex gap-2 items-end max-w-4xl mx-auto">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => { setInput(e.target.value); e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'; }}
            onKeyDown={handleKeyDown}
            placeholder="Ask about this project…"
            rows={1}
            disabled={loading}
            className="flex-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3.5 py-2.5 text-sm resize-none focus:outline-none focus:border-[var(--accent)] disabled:opacity-50 max-h-48"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="shrink-0 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white p-2.5 rounded-lg disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-1.5 text-center">Press Enter to send, Shift+Enter for new line</p>
      </div>

      {/* Evidence Modal */}
      {evidenceModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setEvidenceModal(null)}>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl max-w-lg w-full max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
              <h3 className="font-medium text-sm">Why this answer?</h3>
              <button onClick={() => setEvidenceModal(null)} className="p-1 rounded hover:bg-white/5 text-gray-400"><X size={16} /></button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Answer</p>
                <p className="text-sm text-gray-300 bg-[var(--bg-primary)] rounded-lg p-3">{evidenceModal.content}</p>
              </div>
              {(() => {
                const srcs = (evidenceModal.sources || []) as { memory_type: string; content: string; score: number; memory_id: string }[];
                if (srcs.length === 0) return <p className="text-xs text-gray-500">This answer was generated from general knowledge without specific memory retrieval.</p>;
                return (
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Evidence trail</p>
                    <div className="space-y-2">
                      {srcs.map((s, i) => (
                        <div key={i} className="bg-[var(--bg-primary)] rounded-lg p-3 space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-medium bg-[var(--accent)]/20 text-[var(--accent)] px-2 py-0.5 rounded">{s.memory_type}</span>
                            <span className="text-xs text-gray-500">Score: {Math.round(s.score * 100)}%</span>
                          </div>
                          <p className="text-sm text-gray-300">{s.content}</p>
                          <div className="flex items-center gap-1 text-xs text-gray-600">
                            <span className="font-mono">{s.memory_id.slice(0, 8)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-gray-600 mt-3">
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
