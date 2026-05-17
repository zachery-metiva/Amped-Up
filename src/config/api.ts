const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000';

function cleanBaseUrl(value: string | undefined): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed.replace(/\/+$/, '') : DEFAULT_API_BASE_URL;
}

export const API_BASE_URL = cleanBaseUrl(import.meta.env.VITE_API_BASE_URL);
export const DASHBOARD_API_URL = `${API_BASE_URL}/api/dashboard`;

export const DASHBOARD_WS_URL = (() => {
  const override = import.meta.env.VITE_DASHBOARD_WS_URL?.trim();
  if (override) return override;

  const url = new URL(API_BASE_URL);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = '/api/dashboard/ws';
  url.search = '';
  url.hash = '';
  return url.toString();
})();
