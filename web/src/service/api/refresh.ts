import { http } from '@/service/request';

export interface RefreshFailedListItem {
  id: number;
  email: string;
  error: string;
}

export interface RefreshStats {
  total?: number;
  success?: number;
  failed?: number;
  last_refresh_time?: string | null;
}

export const refreshApi = {
  stats() {
    return http<{ success: boolean; stats: RefreshStats }>({
      method: 'GET',
      url: '/api/accounts/refresh-stats'
    });
  },
  refreshOne(accountId: number) {
    return http<{ success: boolean; error?: string; error_message?: string }>({
      method: 'POST',
      url: `/api/accounts/${accountId}/refresh`
    });
  },
  retryFailed() {
    return http<{
      success: boolean;
      total: number;
      success_count: number;
      failed_count: number;
      failed_list: RefreshFailedListItem[];
    }>({
      method: 'POST',
      url: '/api/accounts/refresh-failed'
    });
  },
  // 初始化选中账号流式任务
  createSelectedTask(account_ids: number[]) {
    return http<{
      success: boolean;
      task_id: string;
      stream_url: string;
      error?: string;
    }>({
      method: 'POST',
      url: '/api/accounts/refresh-selected-stream',
      data: { account_ids }
    });
  },
  logs(params: { page?: number; per_page?: number } = {}) {
    return http<{
      success: boolean;
      total?: number;
      logs?: any[];
    }>({
      method: 'GET',
      url: '/api/accounts/refresh-logs',
      params
    });
  },
  failedLogs() {
    return http<{ success: boolean; logs?: any[] }>({
      method: 'GET',
      url: '/api/accounts/refresh-logs/failed'
    });
  }
};
