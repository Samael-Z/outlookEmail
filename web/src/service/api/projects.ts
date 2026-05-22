import { http } from '@/service/request';

export interface Project {
  project_key: string;
  name: string;
  description?: string;
  total_count?: number;
  available_count?: number;
  claimed_count?: number;
  success_count?: number;
  failed_count?: number;
  use_alias_email?: boolean;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface ProjectAccount {
  account_id: number;
  email: string;
  status: string;
  claim_token?: string;
  caller_id?: string;
  task_id?: string;
  claimed_at?: string;
  detail?: string;
  [key: string]: any;
}

export const projectsApi = {
  list() {
    return http<{ success: boolean; data: { projects: Project[] } }>({
      method: 'GET',
      url: '/api/projects'
    });
  },
  get(key: string) {
    return http<{ success: boolean; data?: { project: Project }; error?: string }>({
      method: 'GET',
      url: `/api/projects/${encodeURIComponent(key)}`
    });
  },
  start(body: {
    project_key: string;
    name?: string;
    description?: string;
    group_ids?: number[];
    use_alias_email?: boolean;
  }) {
    return http<{ success: boolean; message?: string; error?: string; data?: any }>({
      method: 'POST',
      url: '/api/projects/start',
      data: body
    });
  },
  accounts(
    key: string,
    params: { status?: string; group_id?: number; provider?: string; keyword?: string } = {}
  ) {
    return http<{
      success: boolean;
      data?: { accounts: ProjectAccount[]; total: number; [k: string]: any };
      error?: string;
    }>({
      method: 'GET',
      url: `/api/projects/${encodeURIComponent(key)}/accounts`,
      params
    });
  },
  claimRandom(key: string, body: { caller_id?: string; task_id?: string; lease_seconds?: number } = {}) {
    return http<{ success: boolean; data?: ProjectAccount; error?: string }>({
      method: 'POST',
      url: `/api/projects/${encodeURIComponent(key)}/claim-random`,
      data: body
    });
  },
  completeSuccess(key: string, body: { account_id: number; claim_token: string; detail?: string }) {
    return http<{ success: boolean; error?: string }>({
      method: 'POST',
      url: `/api/projects/${encodeURIComponent(key)}/complete-success`,
      data: body
    });
  },
  completeFailed(key: string, body: { account_id: number; claim_token: string; detail?: string }) {
    return http<{ success: boolean; error?: string }>({
      method: 'POST',
      url: `/api/projects/${encodeURIComponent(key)}/complete-failed`,
      data: body
    });
  },
  release(key: string, body: { account_id: number; claim_token: string; detail?: string }) {
    return http<{ success: boolean; error?: string }>({
      method: 'POST',
      url: `/api/projects/${encodeURIComponent(key)}/release`,
      data: body
    });
  },
  resetFailed(key: string, account_id: number, detail = '') {
    return http<{ success: boolean; error?: string }>({
      method: 'POST',
      url: `/api/projects/${encodeURIComponent(key)}/reset-failed`,
      data: { account_id, detail }
    });
  },
  remove(key: string, account_id: number, detail = '') {
    return http<{ success: boolean; error?: string }>({
      method: 'POST',
      url: `/api/projects/${encodeURIComponent(key)}/remove-account`,
      data: { account_id, detail }
    });
  }
};
