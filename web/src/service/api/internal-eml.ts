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

export interface DomainsConfig {
  success: boolean;
  domains: Record<string, string>;
  default_key: string;
  default_key_present: boolean;
}

export interface CreateAccountPayload {
  email: string;
  api_key?: string;
  base_url?: string;
  group_id?: number;
  remark?: string;
}

export interface BulkCreateItem {
  email: string;
  api_key?: string;
  base_url?: string;
}

export const internalEmlApi = {
  getDomains() {
    return http<DomainsConfig>({
      method: 'GET',
      url: '/api/internal-eml/config/domains'
    });
  },
  generateRandom(payload: { domain?: string; prefix_length?: number; group_id?: number; remark?: string } = {}) {
    return http<{
      success: boolean;
      error?: string;
      account?: {
        id: number;
        email: string;
        domain: string;
        base_url: string;
        group_id: number;
        remark: string;
      };
    }>({
      method: 'POST',
      url: '/api/internal-eml/accounts/generate-random',
      data: payload
    });
  },
  createAccount(payload: CreateAccountPayload) {
    return http<{
      success: boolean;
      error?: string;
      account?: {
        id: number;
        email: string;
        account_type: string;
        provider: string;
        imap_host: string;
        group_id: number;
        remark: string;
      };
    }>({
      method: 'POST',
      url: '/api/internal-eml/accounts',
      data: payload
    });
  },
  bulkCreate(items: BulkCreateItem[], group_id?: number, remark?: string) {
    return http<{
      success: boolean;
      created_count: number;
      skipped_count: number;
      created: Array<{ id: number; email: string; base_url: string }>;
      skipped: Array<{ email: string; reason: string }>;
    }>({
      method: 'POST',
      url: '/api/internal-eml/accounts/bulk',
      data: { items, group_id, remark }
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
