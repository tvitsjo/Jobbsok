import api from './client';
import type { Profile } from '../types';

export const getProfile = () => api.get<Profile>('/profile');

export const updateProfile = (data: { free_text?: string }) =>
  api.put<Profile>('/profile', data);

export const uploadCV = (file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api.post<Profile>('/profile/cv', form);
};

export const uploadLinkedIn = (file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api.post<Profile>('/profile/linkedin', form);
};

export const triggerExtraction = () => api.post<Profile>('/profile/extract');

export const updateSkills = (extracted_skills: Record<string, unknown>) =>
  api.put<Profile>('/profile/skills', { extracted_skills });
