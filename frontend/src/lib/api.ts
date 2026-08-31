const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem('sv_tokens');
    return raw ? JSON.parse(raw)?.access_token || null : null;
  } catch { return null; }
}

async function refreshAccessToken(): Promise<string | null> {
  try {
    const raw = localStorage.getItem('sv_tokens');
    if (!raw) return null;
    const tokens = JSON.parse(raw);
    if (!tokens.refresh_token) return null;
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: tokens.refresh_token }),
    });
    if (!res.ok) { clearTokens(); return null; }
    const data = await res.json();
    const updated = { ...tokens, access_token: data.access_token, refresh_token: data.refresh_token ?? tokens.refresh_token };
    localStorage.setItem('sv_tokens', JSON.stringify(updated));
    return data.access_token;
  } catch { return null; }
}

function clearTokens() { localStorage.removeItem('sv_tokens'); }
function storeTokens(tokens: { access_token: string; refresh_token: string }) {
  localStorage.setItem('sv_tokens', JSON.stringify(tokens));
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  let token = getToken();

  const makeRequest = async (authHeader?: string): Promise<Response> => {
    const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
    if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }
    if (authHeader) headers['Authorization'] = `Bearer ${authHeader}`;
    return fetch(url, { ...options, headers, credentials: 'include' });
  };

  let res = await makeRequest(token ?? undefined);

  if (res.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await makeRequest(newToken);
      if (res.status === 401) { clearTokens(); }
    } else {
      clearTokens();
    }
  }

  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try { const json = JSON.parse(text); detail = json.detail || json.message || text; } catch {}
    const err = new Error(detail || `HTTP ${res.status}`) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── REST ────────────────────────────────────────────────────────────

export function apiGet<T>(path: string): Promise<T> { return request<T>(path); }
export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body: body !== undefined ? JSON.stringify(body) : undefined });
}
export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'PATCH', body: JSON.stringify(body) });
}
export function apiDelete<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' });
}

// ── SSE streaming ───────────────────────────────────────────────────

export async function* streamChat(message: string, signal?: AbortSignal): AsyncGenerator<string, void, unknown> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': token ? `Bearer ${token}` : '' },
    body: JSON.stringify({ message }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try { const j = JSON.parse(text); detail = j.detail || text; } catch {}
    throw new Error(detail || `HTTP ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

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
        const event = JSON.parse(payload);
        if (event.type === 'token' && event.content) {
          yield event.content;
        } else if (event.type === 'done') {
          return;
        } else if (event.type === 'error') {
          throw new Error(event.detail || 'Stream error');
        }
      } catch (e) {
        if (e instanceof Error) throw e;
      }
    }
  }
}

// ── Multipart upload ────────────────────────────────────────────────

export async function uploadFile(
  projectId: string,
  file: File,
  onProgress?: (progress: number) => void,
): Promise<{ source_id: string; status: string }> {
  const token = getToken();
  const form = new FormData();
  form.append('project_id', projectId);
  form.append('source_type', file.name.endsWith('.json') ? 'chatgpt' : file.name.endsWith('.jsonl') ? 'jsonl' : 'text');
  form.append('file', file);

  const xhr = new XMLHttpRequest();
  return new Promise((resolve, reject) => {
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total);
    });
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText)); }
        catch (e) { reject(new Error('Invalid response')); }
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`));
      }
    });
    xhr.addEventListener('error', () => reject(new Error('Upload failed')));
    xhr.open('POST', `${API_BASE}/api/v1/ingest/upload`);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.send(form);
  });
}

export { getToken, storeTokens, clearTokens, refreshAccessToken };
