import api from './client';
import type { AdminConfig, JobSource, SystemStats } from '../types';

export const getConfig = () => api.get<AdminConfig[]>('/admin/config');

export const updateConfig = (key: string, value: string) =>
  api.put<AdminConfig>(`/admin/config/${key}`, { value });

export const getSources = () => api.get<JobSource[]>('/admin/sources');

export const updateSource = (id: string, data: { is_enabled?: boolean; config?: Record<string, unknown> }) =>
  api.put<JobSource>(`/admin/sources/${id}`, data);

export const getStats = () => api.get<SystemStats>('/admin/stats');

export const triggerFetch = () => api.post('/admin/trigger-fetch');
