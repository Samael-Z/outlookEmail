import { http } from '@/service/request';

export interface InternalEmlMessage {
  id: number;
  subject: string;
  from_addr: string;
  to_addr: string;
  has_attachment: number;
  received_at: string | null;
  fetched_at: string;
  is_read: number;
}

export interface InternalEmlAttachment {
  filename: string;
  content_type: string;
  size: number;
}

export interface InternalEmlMessageDetail extends InternalEmlMessage {
  body_text: string;
  body_html: string;
  attachments: InternalEmlAttachment[];
}

export const internalEmlApi = {
  getDomains() {
    return http<{ success: boolean; domains: Record<string, string>; default_key_present: boolean }>({
      method: 'GET',
      url: '/api/internal-eml/config/domains'
    });
  },
  refresh(accountId: number) {
    return http<{ success: boolean; fetched: number; deleted: number; error: string | null }>({
      method: 'POST',
      url: `/api/internal-eml/${accountId}/refresh`
    });
  },
  list(accountId: number, params: { page?: number; per_page?: number; keyword?: string } = {}) {
    return http<{
      success: boolean;
      total: number;
      page: number;
      per_page: number;
      messages: InternalEmlMessage[];
    }>({
      method: 'GET',
      url: `/api/internal-eml/${accountId}/messages`,
      params
    });
  },
  detail(accountId: number, msgId: number) {
    return http<{ success: boolean; message: InternalEmlMessageDetail }>({
      method: 'GET',
      url: `/api/internal-eml/${accountId}/messages/${msgId}`
    });
  },
  remove(accountId: number, msgId: number) {
    return http({
      method: 'DELETE',
      url: `/api/internal-eml/${accountId}/messages/${msgId}`
    });
  },
  attachmentUrl(accountId: number, msgId: number, idx: number) {
    return `/api/internal-eml/${accountId}/messages/${msgId}/attachments/${idx}`;
  }
};
