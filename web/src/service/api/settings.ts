import { http } from '@/service/request';

export interface AppSettings {
  external_api_key?: string;
  app_timezone?: string;
  show_account_created_at?: string;
  show_account_sort_order?: string;
  show_group_id?: string;
  login_password_masked?: string;
  [key: string]: any;
}

export const settingsApi = {
  get() {
    return http<{ success: boolean; settings: AppSettings }>({
      method: 'GET',
      url: '/api/settings'
    });
  },
  update(patch: Record<string, any>) {
    return http<{ success: boolean; error?: string; message?: string }>({
      method: 'PUT',
      url: '/api/settings',
      data: patch
    });
  },
  changePassword(newPassword: string) {
    return http<{ success: boolean; error?: string }>({
      method: 'PUT',
      url: '/api/settings',
      data: { login_password: newPassword }
    });
  },
  rotateExternalApiKey(newKey: string) {
    return http<{ success: boolean; error?: string }>({
      method: 'PUT',
      url: '/api/settings',
      data: { external_api_key: newKey }
    });
  }
};
