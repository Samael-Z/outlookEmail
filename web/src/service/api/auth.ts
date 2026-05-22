import { http } from '@/service/request';

export interface LoginResult {
  success: boolean;
  message?: string;
  error?: string;
}

export const authApi = {
  login(password: string) {
    return http<LoginResult>({
      method: 'POST',
      url: '/login',
      data: { password }
    });
  },
  logout() {
    return http({ method: 'GET', url: '/logout' });
  }
};
