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
  listAccounts(groupId?: number) {
    return http<{ success: boolean; accounts: Account[] }>({
      method: 'GET',
      url: '/api/accounts',
      params: groupId ? { group_id: groupId } : undefined
    });
  },
  createAccount(body: Partial<Account> & { password?: string; refresh_token?: string }) {
    return http<{ success: boolean; account?: Account; error?: string }>({
      method: 'POST',
      url: '/api/accounts',
      data: body
    });
  }
};
