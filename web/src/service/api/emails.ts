import { http } from '@/service/request';

export interface EmailListItem {
  id?: string;
  subject?: string;
  from?: { name?: string; address?: string } | string;
  receivedDateTime?: string;
  date?: string;
  hasAttachments?: boolean;
  isRead?: boolean;
  isUnread?: boolean;
  preview?: string;
  bodyPreview?: string;
  folder?: string;
  uid?: string | number;
  id_mode?: string;
}

export type Folder = 'inbox' | 'junkemail' | 'deleteditems' | 'all';

export const emailsApi = {
  list(email: string, params: { folder?: Folder; skip?: number; top?: number } = {}) {
    return http<{
      success: boolean;
      emails?: EmailListItem[];
      error?: any;
      total?: number;
    }>({
      method: 'GET',
      url: `/api/emails/${encodeURIComponent(email)}`,
      params
    });
  },
  detail(email: string, messageId: string) {
    return http<{ success: boolean; email?: any; error?: any }>({
      method: 'GET',
      url: `/api/email/${encodeURIComponent(email)}/${encodeURIComponent(messageId)}`
    });
  },
  markRead(email: string, items: Array<{ id: string; folder?: string; id_mode?: string }>) {
    return http<{ success: boolean; success_count?: number; failed_count?: number; error?: any }>({
      method: 'POST',
      url: '/api/emails/mark-read',
      data: { email, items }
    });
  },
  deleteMany(email: string, ids: string[]) {
    return http<{ success: boolean; success_count?: number; failed_count?: number; error?: any }>({
      method: 'POST',
      url: '/api/emails/delete',
      data: { email, ids }
    });
  }
};
