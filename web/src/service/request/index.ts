import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios';

let csrfToken = '';
let csrfFetching: Promise<string> | null = null;

async function ensureCsrfToken(): Promise<string> {
  if (csrfToken) return csrfToken;
  if (csrfFetching) return csrfFetching;
  csrfFetching = (async () => {
    try {
      const res = await axios.get('/api/csrf-token', { withCredentials: true });
      csrfToken = res.data?.csrf_token || '';
      return csrfToken;
    } catch {
      return '';
    } finally {
      csrfFetching = null;
    }
  })();
  return csrfFetching;
}

const request: AxiosInstance = axios.create({
  baseURL: '/',
  timeout: 60_000,
  withCredentials: true
});

request.interceptors.request.use(async config => {
  const method = (config.method || 'get').toLowerCase();
  if (['post', 'put', 'delete', 'patch'].includes(method)) {
    const token = await ensureCsrfToken();
    if (token) {
      config.headers = config.headers || {};
      (config.headers as any)['X-CSRF-Token'] = token;
      (config.headers as any)['X-CSRFToken'] = token;
    }
  }
  return config;
});

request.interceptors.response.use(
  res => res,
  async error => {
    if (error?.response?.status === 401) {
      const path = window.location.pathname;
      if (path !== '/login') {
        window.location.href = '/login';
      }
    }
    // CSRF 失效时重取一次
    if (error?.response?.status === 400 && /csrf/i.test(JSON.stringify(error.response.data || ''))) {
      csrfToken = '';
    }
    return Promise.reject(error);
  }
);

export async function http<T = any>(config: AxiosRequestConfig): Promise<T> {
  const res = await request.request<T>(config);
  return res.data;
}

export default request;
