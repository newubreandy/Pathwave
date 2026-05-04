/**
 * AuthService — 시설 사장님/직원 인증 (백엔드 /api/facility/* 호출).
 * 모든 HTTP는 공통 apiClient를 통해 처리.
 */
import apiClient from '../apiClient';

const TOKEN_KEY    = 'pathwave_token';
const REFRESH_KEY  = 'pathwave_refresh_token';
const USER_KEY     = 'pathwave_user';

class AuthService {
  /**
   * 시설 사장 로그인.
   * 운영자 미승인(pending) / 정지(suspended) 상태도 명시 메시지로 throw.
   */
  async login(email, password) {
    const data = await apiClient.post('/api/facility/login', { email, password });
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
   * @param {Object} payload — { email, code, password, company_name, business_no,
   *                             manager_name, manager_phone, manager_email }
   */
  async register(payload) {
    const data = await apiClient.post('/api/facility/register', payload);
    return {
      success: true,
      pendingApproval: data.pending_approval ?? true,
      account: data.facility_account,
      message: data.message,
    };
  }

  /** 이메일 인증 코드 발송 */
  sendCode(email) {
    return apiClient.post('/api/facility/send-code', { email });
  }

  /** 인증 코드 검증 (가입 단계) */
  verifyCode(email, code) {
    return apiClient.post('/api/facility/verify-code', { email, code });
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
