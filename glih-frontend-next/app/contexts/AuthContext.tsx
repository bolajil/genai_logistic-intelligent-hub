'use client';
import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface User { id: string; name: string; email: string; role: string; }

interface AuthContextType {
  user:           User | null;
  loading:        boolean;
  login:          (email: string, password: string) => Promise<void>;
  register:       (name: string, email: string, password: string) => Promise<void>;
  logout:         () => void;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);
const API = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:9001';

function setAuthCookie(v: string) {
  document.cookie = `glih_logged_in=${v}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
}
function clearAuthCookie() {
  document.cookie = 'glih_logged_in=; path=/; max-age=0';
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]       = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    try {
      const stored = localStorage.getItem('glih_user');
      const token  = localStorage.getItem('glih_access_token');
      if (stored && token) {
        setUser(JSON.parse(stored));
      } else {
        // Cookie may be stale — clear it so middleware redirects correctly
        clearAuthCookie();
        localStorage.removeItem('glih_user');
        localStorage.removeItem('glih_access_token');
        localStorage.removeItem('glih_refresh_token');
      }
    } catch {
      clearAuthCookie();
      localStorage.removeItem('glih_user');
      localStorage.removeItem('glih_access_token');
      localStorage.removeItem('glih_refresh_token');
    } finally {
      setLoading(false);
    }
  }, []);

  const _save = (data: any) => {
    localStorage.setItem('glih_access_token',  data.access_token);
    localStorage.setItem('glih_refresh_token', data.refresh_token);
    localStorage.setItem('glih_user',          JSON.stringify(data.user));
    setAuthCookie('1');
    setUser(data.user);
  };

  const _fetch = async (path: string, body: object, token?: string) => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res  = await fetch(`${API}${path}`, { method: 'POST', headers, body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail ?? 'Request failed');
    return data;
  };

  const login = useCallback(async (email: string, password: string) => {
    const data = await _fetch('/auth/login', { email, password });
    _save(data);
    if (data.force_password_change) router.push('/change-password');
    else router.push('/dashboard');
  }, [router]);

  const register = useCallback(async (name: string, email: string, password: string) => {
    const data = await _fetch('/auth/register', { name, email, password });
    _save(data);
    router.push('/dashboard');
  }, [router]);

  const logout = useCallback(() => {
    const refresh = localStorage.getItem('glih_refresh_token');
    if (refresh) fetch(`${API}/auth/logout`, { method: 'POST',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refresh }) }).catch(() => {});
    localStorage.removeItem('glih_access_token');
    localStorage.removeItem('glih_refresh_token');
    localStorage.removeItem('glih_user');
    clearAuthCookie();
    setUser(null);
    router.push('/login');
  }, [router]);

  const changePassword = useCallback(async (currentPassword: string, newPassword: string) => {
    const token = localStorage.getItem('glih_access_token');
    await _fetch('/auth/change-password', { current_password: currentPassword, new_password: newPassword }, token ?? undefined);
    // Clear force_password_change so the layout no longer redirects back here
    const stored = localStorage.getItem('glih_user');
    if (stored) {
      try {
        const u = JSON.parse(stored);
        delete u.force_password_change;
        localStorage.setItem('glih_user', JSON.stringify(u));
        setUser(u);
      } catch { /* ignore */ }
    }
    router.push('/dashboard');
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, changePassword }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
