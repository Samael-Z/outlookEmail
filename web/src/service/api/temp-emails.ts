import { http } from '@/service/request';

export interface TempEmail {
  id: number;
  email: string;
  provider: 'gptmail' | 'duckmail' | 'cloudflare';
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TempEmailMessage {
  id?: string;
  subject?: string;
  from?: any;
  date?: string;
  receivedDateTime?: string;
  preview?: string;
}

export const tempEmailsApi = {
  list() {
    return http<{ success: boolean; emails: TempEmail[] }>({
      method: 'GET',
      url: '/api/temp-emails'
    });
  },
  batchDelete(temp_email_ids: number[]) {
    return http<{
      success: boolean;
      message?: string;
      deleted_emails?: Array<{ id: number; email: string }>;
      missing_ids?: number[];
      error?: string;
    }>({
      method: 'POST',
      url: '/api/temp-emails/batch-delete',
      data: { temp_email_ids }
    });
  },
  generate(payload: {
    provider: 'gptmail' | 'duckmail' | 'cloudflare';
    prefix?: string;
    domain?: string;
    username?: string;
    password?: string;
  }) {
    return http<{ success: boolean; email?: string; message?: string; error?: string }>({
      method: 'POST',
      url: '/api/temp-emails/generate',
      data: payload
    });
  },
  delete(email: string) {
    return http<{ success: boolean; error?: string }>({
      method: 'DELETE',
      url: `/api/temp-emails/${encodeURIComponent(email)}`
    });
  },
  messages(email: string) {
    return http<{ success: boolean; messages?: TempEmailMessage[]; emails?: TempEmailMessage[]; error?: string }>({
      method: 'GET',
      url: `/api/temp-emails/${encodeURIComponent(email)}/messages`
    });
  },
  messageDetail(email: string, messageId: string) {
    return http<{ success: boolean; message?: any; email?: any; error?: string }>({
      method: 'GET',
      url: `/api/temp-emails/${encodeURIComponent(email)}/messages/${encodeURIComponent(messageId)}`
    });
  },
  refresh(email: string) {
    return http<{ success: boolean; message?: string; error?: string }>({
      method: 'POST',
      url: `/api/temp-emails/${encodeURIComponent(email)}/refresh`
    });
  },
  duckmailDomains() {
    return http<{
      success: boolean;
      domains: Array<{ id?: string; domain: string }>;
      error?: string;
    }>({ method: 'GET', url: '/api/duckmail/domains' });
  },
  cloudflareDomains() {
    return http<{
      success: boolean;
      domains: Array<{ domain: string }>;
      error?: string;
    }>({ method: 'GET', url: '/api/cloudflare/domains' });
  }
};
