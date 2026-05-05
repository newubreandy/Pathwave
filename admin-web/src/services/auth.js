import apiClient, { TOKEN_KEY, REFRESH_KEY, USER_KEY } from './apiClient.js';

export async function adminLogin(email, password) {
  const data = await apiClient.post('/api/admin/login', { email, password });
  if (data.access_token) localStorage.setItem(TOKEN_KEY, data.access_token);
  else if (data.token) localStorage.setItem(TOKEN_KEY, data.token);
  if (data.refresh_token) localStorage.setItem(REFRESH_KEY, data.refresh_token);
  if (data.admin) localStorage.setItem(USER_KEY, JSON.stringify(data.admin));
  return data;
}

export function adminLogout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getCurrentAdmin() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isAuthenticated() {
  return !!localStorage.getItem(TOKEN_KEY);
}

export async function fetchMe() {
  const data = await apiClient.get('/api/admin/me');
  if (data.admin) localStorage.setItem(USER_KEY, JSON.stringify(data.admin));
  return data.admin;
}
