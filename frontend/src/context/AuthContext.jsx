import { createContext, useContext, useEffect, useState, useCallback } from 'react';

const AuthContext = createContext(null);
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8095';
const TOKEN_KEY = 'smt_onic_auth';

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    try {
      const raw = localStorage.getItem(TOKEN_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(false);

  const persist = useCallback((payload) => {
    if (payload) {
      localStorage.setItem(TOKEN_KEY, JSON.stringify(payload));
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
    setAuth(payload);
  }, []);

  const login = useCallback(async (username, password) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Error de autenticacion' }));
        throw new Error(err.detail || 'Credenciales invalidas');
      }
      const data = await res.json();
      persist({ token: data.access_token, expires_at: data.expires_at, user: data.user });
      return data;
    } finally {
      setLoading(false);
    }
  }, [persist]);

  const logout = useCallback(async () => {
    const token = auth?.token;
    try {
      if (token) {
        await fetch(`${API_BASE}/api/v1/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      }
    } catch { /* ignore */ }
    persist(null);
  }, [auth, persist]);

  const authedFetch = useCallback(async (path, opts = {}) => {
    const token = auth?.token;
    const headers = {
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
    if (res.status === 401) {
      persist(null);
    }
    return res;
  }, [auth, persist]);

  // Validate token on mount (soft check)
  useEffect(() => {
    if (!auth?.token) return;
    const expires = new Date(auth.expires_at).getTime();
    if (Number.isFinite(expires) && expires < Date.now()) {
      persist(null);
    }
  }, [auth, persist]);

  const value = {
    user: auth?.user || null,
    token: auth?.token || null,
    isAuthenticated: Boolean(auth?.token),
    loading,
    login,
    logout,
    authedFetch,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
}
