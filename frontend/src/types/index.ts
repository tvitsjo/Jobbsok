export interface User {
  id: string;
  email: string;
  is_admin: boolean;
  is_active: boolean;
  notification_emails: string[] | null;
  created_at: string;
}

export interface Profile {
  id: string;
  user_id: string;
  cv_file_path: string | null;
  linkedin_image_path: string | null;
  free_text: string | null;
  extracted_skills: Record<string, unknown> | null;
  summary: string | null;
  extraction_status: string;
  last_extracted_at: string | null;
  created_at: string;
}

export interface JobPreference {
  id: string;
  user_id: string;
  job_titles: string[];
  job_types: string[];
  locations: string[];
  min_salary: number | null;
  keywords: string[];
  exclude_keywords: string[];
  is_active: boolean;
  created_at: string;
}

export interface JobListing {
  id: string;
  source_id: string;
  external_id: string;
  title: string;
  company_name: string | null;
  description: string | null;
  location: string | null;
  job_type: string | null;
  salary_info: string | null;
  url: string | null;
  posted_at: string | null;
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface SearchResult {
  id: string;
  job_listing: JobListing;
  relevance_score: number;
  llm_reasoning: string | null;
  is_seen: boolean;
  is_saved: boolean;
  is_dismissed: boolean;
  dismiss_reason: string | null;
  is_notified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AdminConfig {
  key: string;
  value: string;
  updated_at: string;
}

export interface JobSource {
  id: string;
  name: string;
  display_name: string;
  is_enabled: boolean;
  config: Record<string, unknown> | null;
  last_fetched_at: string | null;
  created_at: string;
}

export interface SystemStats {
  total_users: number;
  total_jobs: number;
  total_search_runs: number;
  total_matches: number;
}
