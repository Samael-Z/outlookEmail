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
    // /logout 改为 POST-only（GET 仅展示 SPA shell，不再修改 session）。
    // axios 拦截器会自动附加 X-CSRFToken，避免跨站 GET 触发的登出 DoS。
    return http<{ success: boolean }>({ method: 'POST', url: '/logout' });
  }
};
