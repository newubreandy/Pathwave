/**
 * Admin Web 공통 HTTP 클라이언트.
 * provider-web/src/services/apiClient.js 와 동일 구조.
 *
 * 토큰 키는 별도(`pathwave_admin_token`) 를 사용해서 같은 브라우저에서
 * provider-web 과 admin-web 을 동시에 띄워도 충돌하지 않게 한다.
 */

export const TOKEN_KEY = 'pathwave_admin_token';
export const REFRESH_KEY = 'pathwave_admin_refresh_token';
export const USER_KEY = 'pathwave_admin_user';

function _getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

async function request(path, { method = 'GET', body, headers = {}, raw = false } = {}) {
  const finalHeaders = { 'Content-Type': 'application/json', ...headers };
  const token = _getToken();
  if (token) finalHeaders['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers: finalHeaders };
  if (body !== undefined) opts.body = JSON.stringify(body);

  const resp = await fetch(path, opts);

  if (raw) return resp;

  let data;
  try { data = await resp.json(); } catch { data = {}; }

  if (resp.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    const err = new Error(data.message || '세션이 만료되었습니다. 다시 로그인해 주세요.');
    err.status = 401;
    err.unauthorized = true;
    throw err;
  }

  if (resp.status === 429) {
    const err = new Error(data.message || '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.');
    err.status = 429;
    throw err;
  }

  if (!resp.ok || data.success === false) {
    const err = new Error(data.message || `요청 실패 (${resp.status})`);
    err.status = resp.status;
    err.payload = data;
    throw err;
  }

  return data;
}

export const apiClient = {
  get:    (path, opts)            => request(path, { ...opts, method: 'GET' }),
  post:   (path, body, opts)      => request(path, { ...opts, method: 'POST', body }),
  put:    (path, body, opts)      => request(path, { ...opts, method: 'PUT', body }),
  patch:  (path, body, opts)      => request(path, { ...opts, method: 'PATCH', body }),
  delete: (path, opts)            => request(path, { ...opts, method: 'DELETE' }),
};

export default apiClient;
