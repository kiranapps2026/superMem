'use client';
import { useEffect, useState, useRef } from 'react';
import { apiGet, apiPost } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useParams } from 'next/navigation';
import { MessageSquare, Send, User, Bot, Shield, ShieldOff, ShieldQuestion } from 'lucide-react';
import { useSSE } from '@/hooks/useSSE';

const CONFICENCE_COLORS: Record<string, string> = { high: 'text-green-400', medium: 'text-yellow-400', low: 'text-red-400', unknown: 'text-gray-500' };
const CONFICENCE_ICONS: Record<string, React.ReactNode> = { high: <Shield size={12} />, medium: <ShieldQuestion size={12} />, low: <ShieldOff size={12} /> };

export default function ChatPage() {
  const { user } = useAuth();
  const params = useParams();
  const projectId = params.id as string;
  const [messages, setMessages] = useState<{ role: string; content: string; sources?: { memory_id: string; type: string; authority: string; confidence: number; status: string }[] }[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<{ memory_id: string; type: string; authority: string; confidence: number; status: string }[]>([]);
  const [tokens, setTokens] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { stream, stop } = useSSE();

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: 'user', content: input.trim() };
    setMessages((m) => [...m, userMsg]); setInput(''); setLoading(true); setSources([]); setTokens('');
    const assistantContent = ''; setMessages((m) => [...m, { role: 'assistant', content: '' }]);

    stream(
      `/api/v1/chat/stream?project_id=${projectId}`,
      (event) => {
        if (event.type === 'token') {
          setMessages((m) => { const copy = [...m]; copy[copy.length - 1] = { ...copy[copy.length - 1], content: copy[copy.length - 1].content + (event as { content: string }).content }; return copy; });
        } else if (event.type === 'sources') {
          setSources((event as { items: typeof sources }).items);
        }
      },
      (meta) => setTokens(String(meta.tokens)),
      (detail) => { setMessages((m) => { const copy = [...m]; copy[copy.length - 1] = { ...copy[copy.length - 1], content: copy[copy.length - 1].content || `Error: ${detail}` }; return copy; }); setLoading(false); },
    );

    await apiPost('/api/v1/chat/messages', { project_id: projectId, message: userMsg.content }).catch(() => {});
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-[var(--border)]">
        <h1 className="font-semibold text-sm">Chat</h1>
        <p className="text-xs text-gray-500">Grounded in project memory</p>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-20"><MessageSquare size={40} className="mx-auto text-gray-600 mb-3" /><p className="text-gray-500 text-sm">Ask anything about this project&apos;s memory.</p></div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${m.role === 'user' ? 'bg-[var(--accent)]' : 'bg-[var(--bg-tertiary)]'}`}>
              {m.role === 'user' ? <User size={14} className="text-white" /> : <Bot size={14} className="text-gray-400" />}
            </div>
            <div className={`max-w-[70%] px-3 py-2 rounded-lg text-sm whitespace-pre-wrap ${m.role === 'user' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-secondary)] border border-[var(--border)]'}`}>
              {m.content || <span className="text-gray-500 italic">Thinking…</span>}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      {sources.length > 0 && (
        <div className="px-4 py-2 border-t border-[var(--border)]">
          <p className="text-xs text-gray-500 mb-1">Sources</p>
          <div className="flex flex-wrap gap-1.5">
            {sources.map((s) => (
              <span key={s.memory_id} className="inline-flex items-center gap-1 bg-[var(--bg-tertiary)] text-xs px-2 py-0.5 rounded-full text-gray-400">
                {CONFICENCE_ICONS[s.confidence] || <ShieldQuestion size={12} />}
                {s.type}:{s.authority}
                <span className={`${CONFICENCE_COLORS[s.confidence] || 'text-gray-500'}`}>{s.confidence}</span>
              </span>
            ))}
          </div>
        </div>
      )}
      {tokens && <div className="px-4 text-xs text-gray-500">{tokens} tokens</div>}
      <div className="border-t border-[var(--border)] p-3">
        <div className="flex gap-2">
          <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
            placeholder="Ask about this project…" rows={1} disabled={loading}
            className="flex-1 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-md px-3 py-2 text-sm resize-none focus:outline-none focus:border-[var(--accent)] disabled:opacity-50" />
          <button onClick={sendMessage} disabled={loading || !input.trim()}
            className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-3 rounded-md disabled:opacity-50 transition-colors">
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}