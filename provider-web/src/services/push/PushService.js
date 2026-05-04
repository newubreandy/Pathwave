/**
 * PushService — 푸시 토큰 등록/관리 백엔드 연동.
 *
 * 백엔드: routes/push.py — /api/users/me/push-tokens
 *   POST   /api/users/me/push-tokens — 토큰 등록 (FCM/APNs)
 *   GET    /api/users/me/push-tokens — 등록된 토큰 목록
 *   DELETE /api/users/me/push-tokens — 토큰 해제
 *
 * 시설 사장님 웹 클라이언트에서도 사용 가능 (관리자 알림 수신 용도).
 */
import apiClient from '../apiClient';

const PushService = {
  /**
   * 푸시 토큰 등록 / 갱신.
   * @param {Object} payload — { token, platform: 'web'|'android'|'ios' }
   */
  registerToken(payload) {
    return apiClient.post('/api/users/me/push-tokens', payload);
  },

  /** 등록된 토큰 목록 */
  listTokens() {
    return apiClient.get('/api/users/me/push-tokens');
  },

  /** 토큰 해제 */
  unregister(token) {
    return apiClient.delete(`/api/users/me/push-tokens?token=${encodeURIComponent(token)}`);
  },
};

export default PushService;
