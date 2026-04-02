import api from './client';
import type { SearchResult, JobPreference } from '../types';

export const getJobs = (params?: {
  min_score?: number;
  saved_only?: boolean;
  hide_dismissed?: boolean;
  limit?: number;
  offset?: number;
}) => api.get<SearchResult[]>('/jobs', { params });

export const getJob = (id: string) => api.get<SearchResult>(`/jobs/${id}`);

export const toggleSave = (id: string) => api.post(`/jobs/${id}/save`);

export const dismissJob = (id: string, reason: string) =>
  api.post(`/jobs/${id}/dismiss`, { reason });

export const triggerSearch = () => api.post('/jobs/search');

// Preferences
export const getPreferences = () => api.get<JobPreference[]>('/preferences');

export const createPreference = (data: Partial<JobPreference>) =>
  api.post<JobPreference>('/preferences', data);

export const updatePreference = (id: string, data: Partial<JobPreference>) =>
  api.put<JobPreference>(`/preferences/${id}`, data);

export const deletePreference = (id: string) =>
  api.delete(`/preferences/${id}`);

// Notification settings
export const updateNotificationSettings = (notification_emails: string[]) =>
  api.put('/users/notification-settings', { notification_emails });
