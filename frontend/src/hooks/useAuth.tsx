'use client';
import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { TokenPair, UserInfo } from '@/types/api';
import { apiGet, apiPost } from '@/lib/api';

interface AuthState {
  user: UserInfo | null;
  accessToken: string | null;
  refreshToken: string | null;
  loading: boolean;
  error: string | null;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null, accessToken: null, refreshToken: null, loading: true, error: null,
  });

  useEffect(() => {
    apiGet<{ id: string; email: string; name: string | null }>('/api/v1/auth/me')
      .then((user) => setState((s) => ({ ...s, user: { ...user, workspace_id: '', tenant_id: '' }, loading: false })))
      .catch(() => setState((s) => ({ ...s, loading: false })));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await apiPost<TokenPair>('/api/v1/auth/login', { email, password });
      setState({ user: data.user, accessToken: data.access_token, refreshToken: data.refresh_token, loading: false, error: null });
    } catch (err) {
      setState((s) => ({ ...s, loading: false, error: err instanceof Error ? err.message : 'Login failed' }));
      throw err;
    }
  }, []);

  const register = useCallback(async (email: string, password: string, name?: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await apiPost<TokenPair>('/api/v1/auth/register', { email, password, name });
      setState({ user: data.user, accessToken: data.access_token, refreshToken: data.refresh_token, loading: false, error: null });
    } catch (err) {
      setState((s) => ({ ...s, loading: false, error: err instanceof Error ? err.message : 'Registration failed' }));
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    try { await apiPost('/api/v1/auth/logout', {}); } catch {}
    setState({ user: null, accessToken: null, refreshToken: null, loading: false, error: null });
  }, []);

  const refresh = useCallback(async () => {
    if (!state.refreshToken) return;
    try {
      const data = await apiPost<TokenPair>('/api/v1/auth/refresh', { token: state.refreshToken });
      setState((s) => ({ ...s, accessToken: data.access_token, refreshToken: data.refresh_token, error: null }));
    } catch {
      setState({ user: null, accessToken: null, refreshToken: null, loading: false, error: null });
    }
  }, [state.refreshToken]);

  const clearError = useCallback(() => { setState((s) => ({ ...s, error: null })); }, []);

  return <AuthContext.Provider value={{ ...state, login, register, logout, refresh, clearError }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
