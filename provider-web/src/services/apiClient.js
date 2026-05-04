/**
 * 공통 HTTP 클라이언트 — 모든 service의 백엔드 호출을 통일.
 *
 * 자동 처리:
 *  - localStorage 토큰을 Authorization 헤더에 자동 주입
 *  - JSON 직렬화 / 역직렬화
 *  - 401(만료) 시 자동 로그아웃 + /login 리다이렉트 (옵션)
 *  - 백엔드 에러 메시지를 throw 가능한 Error로 변환
 */

const TOKEN_KEY = 'pathwave_token';

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

  if (raw) return resp;   // 호출자가 직접 파싱 (예: 파일 다운로드)

  let data;
  try { data = await resp.json(); } catch { data = {}; }

  if (resp.status === 401) {
    // 토큰 만료/무효 → 자동 로그아웃 (소프트 처리: redirect는 라우터가 결정)
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('pathwave_user');
    localStorage.removeItem('pathwave_refresh_token');
    const err = new Error(data.message || '세션이 만료되었습니다. 다시 로그인해 주세요.');
    err.status = 401;
    err.unauthorized = true;
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
