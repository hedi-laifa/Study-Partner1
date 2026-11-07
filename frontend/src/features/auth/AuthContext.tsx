import React, { createContext, useContext, useEffect, useState } from 'react';
import authService, { type LoginPayload, type RegisterPayload } from '../../services/authService';

export interface User {
  id: number;
  email: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (data: LoginPayload) => Promise<void>;
  register: (data: RegisterPayload) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const email = localStorage.getItem('userEmail');
    const id = localStorage.getItem('userId');
    if (email && id) {
      return { id: Number(id), email };
    }
    return null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      const me = await authService.getMe();
      setUser(me);
    } catch {
      // If unauthorized or token invalid, don't crash
    }
  };

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      refreshUser().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (data: LoginPayload) => {
    setLoading(true);
    try {
      const res = await authService.login(data);
      const authToken = res.token || res.access_token || null;
      setToken(authToken);
      const userId = res.user_id || res.id || (res.user as any)?.id || 1;
      setUser({ id: Number(userId), email: data.email });
    } finally {
      setLoading(false);
    }
  };

  const register = async (data: RegisterPayload) => {
    setLoading(true);
    try {
      await authService.register(data);
      // Auto login after registration
      await login(data);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token || !!user,
        loading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
