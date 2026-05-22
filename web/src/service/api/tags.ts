import { http } from '@/service/request';

export interface Tag {
  id: number;
  name: string;
  color: string;
}

export const tagsApi = {
  list() {
    return http<{ success: boolean; tags: Tag[] }>({ method: 'GET', url: '/api/tags' });
  },
  create(body: { name: string; color?: string }) {
    return http<{ success: boolean; tag?: Tag; error?: string }>({
      method: 'POST',
      url: '/api/tags',
      data: body
    });
  },
  delete(id: number) {
    return http<{ success: boolean; error?: string }>({
      method: 'DELETE',
      url: `/api/tags/${id}`
    });
  },
  batchApply(account_ids: number[], tag_id: number, action: 'add' | 'remove') {
    return http<{ success: boolean; message?: string; error?: string }>({
      method: 'POST',
      url: '/api/accounts/tags',
      data: { account_ids, tag_id, action }
    });
  },
  batchUpdateGroup(account_ids: number[], group_id: number) {
    return http<{ success: boolean; message?: string; error?: string }>({
      method: 'POST',
      url: '/api/accounts/batch-update-group',
      data: { account_ids, group_id }
    });
  },
  batchUpdateForwarding(account_ids: number[], forward_enabled: boolean) {
    return http<{ success: boolean; message?: string; error?: string }>({
      method: 'POST',
      url: '/api/accounts/batch-update-forwarding',
      data: { account_ids, forward_enabled }
    });
  }
};
