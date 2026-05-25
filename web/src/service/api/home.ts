import { http } from '@/service/request';

export interface HomeStats {
  success: boolean;
  totals: {
    accounts: number;
    outlook: number;
    imap: number;
    internal_eml: number;
    active: number;
    forwarding: number;
    groups: number;
    temp_emails: number;
  };
  internal_eml_daily: Array<{ date: string; count: number }>;
  refresh_recent: { success: number; failed: number };
}

export const homeApi = {
  stats() {
    return http<HomeStats>({ method: 'GET', url: '/api/home/stats' });
  }
};
