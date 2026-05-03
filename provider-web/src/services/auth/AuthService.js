/**
 * AuthService
 * 1차 백엔드 모듈: 회원가입, 로그인, 로그아웃 등 인증 관련 비즈니스 로직 처리
 * 추후 Supabase/Firebase Auth, 또는 Node.js JWT API로 교체될 예정입니다.
 */
class AuthService {
  /**
   * 로그인 처리
   * @param {string} email 
   * @param {string} password 
   * @returns {Promise<Object>} user 정보와 토큰
   */
  async login(email, password) {
    // TODO: 실제 API 호출 로직으로 교체
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (email && password) {
          const mockUser = {
            id: 'u123',
            email,
            name: 'Provider Admin',
            role: 'provider',
            accessToken: 'mock_jwt_token_123'
          };
          // 로컬 스토리지 등에 세션 저장 로직 (모의)
          localStorage.setItem('pathwave_token', mockUser.accessToken);
          localStorage.setItem('pathwave_user', JSON.stringify(mockUser));
          resolve({ user: mockUser, success: true });
        } else {
          reject(new Error('Invalid credentials'));
        }
      }, 800);
    });
  }

  /**
   * 이메일 회원가입
   * @param {Object} userData 
   * @returns {Promise<Object>} 생성된 user 정보
   */
  async register(userData) {
    // TODO: 실제 회원가입 API 호출 로직
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockUser = {
          id: 'u' + Date.now(),
          email: userData.email,
          name: userData.ownerName || 'New User',
          role: 'provider',
          accessToken: 'mock_jwt_token_new'
        };
        localStorage.setItem('pathwave_token', mockUser.accessToken);
        localStorage.setItem('pathwave_user', JSON.stringify(mockUser));
        resolve({ user: mockUser, success: true });
      }, 1000);
    });
  }

  /**
   * 로그아웃
   */
  async logout() {
    return new Promise((resolve) => {
      setTimeout(() => {
        localStorage.removeItem('pathwave_token');
        localStorage.removeItem('pathwave_user');
        resolve({ success: true });
      }, 300);
    });
  }

  /**
   * 현재 인증된 유저 정보 가져오기
   */
  getCurrentUser() {
    try {
      const userStr = localStorage.getItem('pathwave_user');
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  }
}

export default new AuthService();
