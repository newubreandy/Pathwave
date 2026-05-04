/**
 * AuthService — 시설 사장님/직원 인증 (백엔드 /api/facility/* 호출).
 *
 * 백엔드 응답 예시 (success):
 *   {
 *     success: true,
 *     access_token: "...",
 *     refresh_token: "...",
 *     facility_account: { id, company_name, email },
 *   }
 */

const TOKEN_KEY = 'pathwave_token';
const REFRESH_KEY = 'pathwave_refresh_token';
const USER_KEY = 'pathwave_user';

async function _request(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const resp = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data;
  try { data = await resp.json(); } catch { data = {}; }
  if (!resp.ok || data.success === false) {
    const err = new Error(data.message || `요청 실패 (${resp.status})`);
    err.status = resp.status;
    err.payload = data;
    throw err;
  }
  return data;
}

class AuthService {
  /**
   * 시설 사장님 로그인.
   * 운영자 미승인(pending) / 정지(suspended) 상태도 명시 메시지 포함된 에러로 throw.
   */
  async login(email, password) {
    const data = await _request('/api/facility/login', {
      method: 'POST',
      body: { email, password },
    });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    if (data.refresh_token) localStorage.setItem(REFRESH_KEY, data.refresh_token);
    const user = {
      id: data.facility_account.id,
      email: data.facility_account.email,
      name: data.facility_account.company_name,
      role: 'facility',
      accessToken: data.access_token,
    };
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    return { user, success: true };
  }

  /**
   * 시설 회원가입 — 운영자 승인 대기 상태로 생성.
   * @param {Object} payload — { email, code, password, company_name, business_no, manager_name, manager_phone, manager_email }
   */
  async register(payload) {
    const data = await _request('/api/facility/register', {
      method: 'POST',
      body: payload,
    });
    return {
      success: true,
      pendingApproval: data.pending_approval ?? true,
      account: data.facility_account,
      message: data.message,
    };
  }

  /** 이메일 인증 코드 발송 */
  async sendCode(email) {
    return _request('/api/facility/send-code', {
      method: 'POST',
      body: { email },
    });
  }

  /** 인증 코드 검증 (가입 단계) */
  async verifyCode(email, code) {
    return _request('/api/facility/verify-code', {
      method: 'POST',
      body: { email, code },
    });
  }

  async logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    return { success: true };
  }

  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  getCurrentUser() {
    try {
      const userStr = localStorage.getItem(USER_KEY);
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  }

  isAuthenticated() {
    return !!this.getToken();
  }
}

export default new AuthService();
