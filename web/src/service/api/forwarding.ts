import { http } from '@/service/request';

export interface ForwardChannelConfig {
  smtp?: {
    smtp_host?: string;
    smtp_port?: number | string;
    smtp_username?: string;
    smtp_password?: string;
    smtp_from_email?: string;
    email_forward_recipient?: string;
    smtp_use_ssl?: string;
    smtp_use_tls?: string;
  };
  telegram?: {
    telegram_bot_token?: string;
    telegram_chat_id?: string;
    telegram_proxy_url?: string;
  };
  wecom?: {
    wecom_webhook_url?: string;
  };
}

export const forwardingApi = {
  testChannel(channel: 'smtp' | 'telegram' | 'wecom', config: ForwardChannelConfig) {
    return http<{ success: boolean; message?: string; error?: string }>({
      method: 'POST',
      url: '/api/settings/test-forward-channel',
      data: { channel, config }
    });
  },
  triggerCheck() {
    return http<{ success: boolean; message?: string; error?: string }>({
      method: 'POST',
      url: '/api/accounts/trigger-forwarding-check'
    });
  },
  resetCursor(accountId: number) {
    return http<{ success: boolean; error?: string }>({
      method: 'POST',
      url: `/api/accounts/${accountId}/forwarding/reset-cursor`
    });
  },
  logs(params: { page?: number; per_page?: number } = {}) {
    return http<{ success: boolean; logs?: any[]; total?: number }>({
      method: 'GET',
      url: '/api/accounts/forwarding-logs',
      params
    });
  },
  failedLogs() {
    return http<{ success: boolean; logs?: any[] }>({
      method: 'GET',
      url: '/api/accounts/forwarding-logs/failed'
    });
  }
};

export const webdavApi = {
  testBackup(config: { url: string; username?: string; password?: string }) {
    return http<{ success: boolean; message?: string; error?: string }>({
      method: 'POST',
      url: '/api/settings/test-webdav-backup',
      data: { config }
    });
  },
  uploadBackup(verify_password: string) {
    return http<{ success: boolean; message?: string; error?: string; filename?: string }>({
      method: 'POST',
      url: '/api/settings/upload-webdav-backup',
      data: { verify_password }
    });
  },
  validateCron(cron: string, timezone?: string) {
    return http<{ success: boolean; preview?: any; error?: string }>({
      method: 'POST',
      url: '/api/settings/validate-cron',
      data: { cron, timezone }
    });
  }
};
