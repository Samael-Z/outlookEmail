import { http } from '@/service/request';

export interface AuditLog {
  id: number;
  action: string;
  resource_type: string;
  resource_id: string | null;
  user_ip: string | null;
  details: string | null;
  created_at: string;
}

export interface DockerUpdateState {
  status?: string;
  message?: string;
  started_at?: string | null;
  finished_at?: string | null;
  log?: string[];
  attempts?: number;
  applied?: boolean;
}

export interface DockerUpdateConfig {
  enabled: boolean;
  available: boolean;
  reason: string;
  socket_path?: string;
  container?: string;
  current_image?: string;
  watchtower_image?: string;
  api_version?: string;
  state: DockerUpdateState;
}

export const systemApi = {
  auditLogs(params: {
    page?: number;
    per_page?: number;
    action?: string;
    resource_type?: string;
    keyword?: string;
  } = {}) {
    return http<{
      success: boolean;
      total: number;
      page: number;
      per_page: number;
      logs: AuditLog[];
      distinct_actions: string[];
      distinct_resource_types: string[];
    }>({
      method: 'GET',
      url: '/api/audit-logs',
      params
    });
  },
  versionStatus(refresh = false) {
    return http<{ success: boolean; version_status: any }>({
      method: 'GET',
      url: '/api/version-status',
      params: refresh ? { refresh: '1' } : undefined
    });
  },
  dockerUpdateStatus() {
    return http<{ success: boolean; docker_update: DockerUpdateConfig }>({
      method: 'GET',
      url: '/api/docker-update/status'
    });
  },
  startDockerUpdate() {
    return http<{ success: boolean; message?: string; error?: string; docker_update?: DockerUpdateConfig }>({
      method: 'POST',
      url: '/api/docker-update'
    });
  }
};
