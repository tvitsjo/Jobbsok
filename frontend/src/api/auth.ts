import api from './client';
import type { TokenResponse, User } from '../types';

export const register = (email: string, password: string) =>
  api.post<User>('/auth/register', { email, password });

export const login = async (email: string, password: string) => {
  const { data } = await api.post<TokenResponse>('/auth/login', { email, password });
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return data;
};

export const getMe = () => api.get<User>('/auth/me');

export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};
