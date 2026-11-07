import apiClient from './apiClient';

export interface RegisterPayload {
  email: string;
  password: string;
  [key: string]: unknown;
}

export interface LoginPayload {
  email: string;
  password: string;
  [key: string]: unknown;
}

export interface AuthResponse {
  id?: number;
  user_id?: number;
  email?: string;
  token?: string;
  access_token?: string;
  user?: {
    id: number;
    email: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export const register = async (data: RegisterPayload): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/auth/register', data);
  const token = response.data.token || response.data.access_token;
  if (token) {
    localStorage.setItem('token', token);
  }
  const userId = response.data.id || response.data.user_id || response.data.user?.id;
  if (userId) {
    localStorage.setItem('userId', String(userId));
  }
  if (data.email) {
    localStorage.setItem('userEmail', data.email);
  }
  return response.data;
};

export const login = async (data: LoginPayload): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/auth/login', data);
  const token = response.data.token || response.data.access_token;
  if (token) {
    localStorage.setItem('token', token);
  }
  const userId = response.data.user_id || response.data.id || response.data.user?.id;
  if (userId) {
    localStorage.setItem('userId', String(userId));
  }
  if (data.email) {
    localStorage.setItem('userEmail', data.email);
  }
  return response.data;
};

export const getMe = async (): Promise<{ id: number; email: string }> => {
  const response = await apiClient.get<{ id: number; email: string }>('/auth/me');
  if (response.data.email) {
    localStorage.setItem('userEmail', response.data.email);
  }
  if (response.data.id) {
    localStorage.setItem('userId', String(response.data.id));
  }
  return response.data;
};

export const logout = (): void => {
  localStorage.removeItem('token');
  localStorage.removeItem('userId');
  localStorage.removeItem('userEmail');
};

export default {
  register,
  login,
  getMe,
  logout,
};
