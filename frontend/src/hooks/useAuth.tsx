'use client';
import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { UserInfo, TokenPair, RegisterRequest } from '@/types/api';
import { apiGet, apiPost, storeTokens, clearTokens, getToken } from '@/lib/api';

interface AuthState {
  user: UserInfo | null;
  loading: boolean;
  error: string | null;
}
interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, loading: true, error: null });

  useEffect(() => {
    (async () => {
      try {
        const data = await apiGet<{ id: string; email: string; name: string | null; workspace_id: string; tenant_id: string }>('/api/v1/auth/me');
        setState({ user: data, loading: false, error: null });
      } catch { setState({ user: null, loading: false, error: null }); }
    })();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    const data = await apiPost<TokenPair>('/api/v1/auth/login', { email, password });
    storeTokens(data);
    setState({ user: data.user, loading: false, error: null });
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    const res = await apiPost<TokenPair & { user: UserInfo }>('/api/v1/auth/register', data);
    setState({ user: res.user, loading: false, error: null });
  }, []);

  const logout = useCallback(async () => {
    try { await apiPost('/api/v1/auth/logout', {}); } catch {}
    clearTokens();
    setState({ user: null, loading: false, error: null });
  }, []);

  const clearError = useCallback(() => setState((s) => ({ ...s, error: null })), []);

  return <AuthContext.Provider value={{ ...state, login, register, logout, clearError }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
