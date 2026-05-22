import { http } from '@/service/request';

export interface Account {
  id: number;
  email: string;
  remark: string | null;
  status: string;
  account_type: string;
  provider: string;
  group_id: number | null;
  imap_host?: string | null;
  imap_password?: string | null;
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
  deleteAccount(id: number) {
    return http<{ success: boolean; error?: string }>({
      method: 'DELETE',
      url: `/api/accounts/${id}`
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
