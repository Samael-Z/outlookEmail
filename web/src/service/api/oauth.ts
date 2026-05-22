import { http } from '@/service/request';

export const oauthApi = {
  getAuthUrl() {
    return http<{
      success: boolean;
      auth_url: string;
      client_id: string;
      redirect_uri: string;
    }>({ method: 'GET', url: '/api/oauth/auth-url' });
  },
  exchangeToken(redirected_url: string) {
    return http<{
      success: boolean;
      refresh_token?: string;
      client_id?: string;
      token_type?: string;
      expires_in?: number;
      scope?: string;
      error?: string;
    }>({
      method: 'POST',
      url: '/api/oauth/exchange-token',
      data: { redirected_url }
    });
  }
};
