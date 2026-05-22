import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig
} from 'axios';

let csrfToken = '';
let csrfFetching: Promise<string> | null = null;
let csrfDisabled = false;

interface RetriableConfig extends InternalAxiosRequestConfig {
  _csrfRetried?: boolean;
}

async function ensureCsrfToken(force = false): Promise<string> {
  if (csrfDisabled) return '';
  if (!force && csrfToken) return csrfToken;
  if (csrfFetching) return csrfFetching;
  csrfFetching = (async () => {
    try {
      const res = await axios.get('/api/csrf-token', { withCredentials: true });
      if (res.data?.csrf_disabled) {
        csrfDisabled = true;
        csrfToken = '';
        return '';
      }
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

function applyCsrfHeader(config: InternalAxiosRequestConfig, token: string) {
  if (!token) return;
  config.headers = config.headers || ({} as any);
  (config.headers as any)['X-CSRF-Token'] = token;
  (config.headers as any)['X-CSRFToken'] = token;
}

request.interceptors.request.use(async config => {
  const method = (config.method || 'get').toLowerCase();
  if (['post', 'put', 'delete', 'patch'].includes(method)) {
    const token = await ensureCsrfToken();
    applyCsrfHeader(config, token);
  }
  return config;
});

request.interceptors.response.use(
  res => res,
  async error => {
    const status = error?.response?.status;

    if (status === 401) {
      const path = window.location.pathname;
      if (path !== '/login') {
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }

    // CSRF token 失效（典型 400/403 + 响应体提到 csrf）：清缓存、刷新、重放一次。
    // 老版本只是清缓存就把错误抛回去，导致用户必须手动重试。
    const isCsrfError =
      (status === 400 || status === 403) &&
      /csrf/i.test(JSON.stringify(error.response?.data ?? ''));
    if (isCsrfError) {
      const originalConfig = error.config as RetriableConfig | undefined;
      csrfToken = '';
      if (originalConfig && !originalConfig._csrfRetried) {
        originalConfig._csrfRetried = true;
        const fresh = await ensureCsrfToken(true);
        if (fresh) applyCsrfHeader(originalConfig, fresh);
        return request.request(originalConfig);
      }
    }

    return Promise.reject(error);
  }
);

export async function http<T = any>(config: AxiosRequestConfig): Promise<T> {
  const res = await request.request<T>(config);
  return res.data;
}

export default request;
