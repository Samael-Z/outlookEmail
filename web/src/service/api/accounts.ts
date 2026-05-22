import { http } from '@/service/request';
import type { Tag } from './tags';

export interface Account {
  id: number;
  email: string;
  remark: string | null;
  status: string;
  account_type: string;
  provider: string;
  group_id: number | null;
  group_name?: string;
  group_color?: string;
  imap_host?: string | null;
  imap_password?: string | null;
  forward_enabled?: boolean;
  tags?: Tag[];
  last_refresh_at?: string | null;
  last_refresh_status?: string | null;
}

export interface Group {
  id: number;
  name: string;
  description: string | null;
  color: string;
  sort_order: number;
  is_system: number;
}

export const accountsApi = {
  listGroups() {
    return http<{ success: boolean; groups: Group[] }>({
      method: 'GET',
      url: '/api/groups'
    });
  },
  search(q: string, limit = 20) {
    return http<{ success: boolean; accounts: Account[]; total: number }>({
      method: 'GET',
      url: '/api/accounts/search',
      params: { q, limit }
    });
  },
  listAccounts(params: { group_id?: number; limit?: number; offset?: number; keyword?: string } | number = {}) {
    const p = typeof params === 'number' ? { group_id: params } : params;
    return http<{
      success: boolean;
      accounts: Account[];
      total: number;
      limit: number;
      offset: number;
      has_more: boolean;
    }>({
      method: 'GET',
      url: '/api/accounts',
      params: p
    });
  },
  createGroup(body: { name: string; description?: string; color?: string; proxy_url?: string }) {
    return http<{ success: boolean; group_id?: number; error?: string; message?: string }>({
      method: 'POST',
      url: '/api/groups',
      data: body
    });
  },
  updateGroup(id: number, body: { name?: string; description?: string; color?: string; proxy_url?: string }) {
    return http<{ success: boolean; error?: string; message?: string }>({
      method: 'PUT',
      url: `/api/groups/${id}`,
      data: body
    });
  },
  deleteGroup(id: number) {
    return http<{ success: boolean; error?: string }>({
      method: 'DELETE',
      url: `/api/groups/${id}`
    });
  },
  createAccount(body: Partial<Account> & { password?: string; refresh_token?: string }) {
    return http<{ success: boolean; account?: Account; error?: string }>({
      method: 'POST',
      url: '/api/accounts',
      data: body
    });
  },
  /**
   * 批量导入账号（Outlook OAuth / IMAP）。
   * - provider: outlook / gmail / qq / 163 / 126 / yahoo / aliyun / custom
   * - account_format: client_id_refresh_token | refresh_token_client_id
   *   (仅 outlook 用)
   * - imap_host/imap_port: 仅 provider=custom 时生效（每行格式 email----pwd 时使用）
   */
  bulkImport(body: {
    account_string: string;
    provider: string;
    group_id?: number;
    account_format?: string;
    imap_host?: string;
    imap_port?: number;
    remark?: string;
  }) {
    return http<{
      success: boolean;
      message?: string;
      added_count?: number;
      skipped_count?: number;
      invalid_count?: number;
      error?: string;
    }>({
      method: 'POST',
      url: '/api/accounts',
      data: body
    });
  },
  getAccount(id: number) {
    return http<{ success: boolean; account?: any; error?: string }>({
      method: 'GET',
      url: `/api/accounts/${id}`
    });
  },
  updateAccount(id: number, body: Record<string, any>) {
    return http<{ success: boolean; message?: string; error?: string; aliases?: string[] }>({
      method: 'PUT',
      url: `/api/accounts/${id}`,
      data: body
    });
  },
  deleteAccount(id: number) {
    return http<{ success: boolean; error?: string }>({
      method: 'DELETE',
      url: `/api/accounts/${id}`
    });
  },
  getAliases(id: number) {
    return http<{ success: boolean; aliases?: string[]; error?: string }>({
      method: 'GET',
      url: `/api/accounts/${id}/aliases`
    });
  },
  updateAliases(id: number, aliases: string[]) {
    return http<{ success: boolean; aliases?: string[]; error?: string; errors?: string[] }>({
      method: 'PUT',
      url: `/api/accounts/${id}/aliases`,
      data: { aliases }
    });
  },
  verifyExportPassword(password: string) {
    return http<{ success: boolean; verify_token?: string; error?: string }>({
      method: 'POST',
      url: '/api/export/verify',
      data: { password }
    });
  },
  batchDelete(ids: number[]) {
    return http<{
      success: boolean;
      message?: string;
      deleted_count?: number;
      deleted_accounts?: number[];
      missing_ids?: number[];
    }>({
      method: 'POST',
      url: '/api/accounts/batch-delete',
      data: { account_ids: ids }
    });
  }
};
