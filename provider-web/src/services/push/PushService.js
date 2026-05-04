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

  // ── 레거시 호환 shim (Notifications.jsx) ─────────────────────────────────
  /** 브라우저 푸시 권한 요청 (실제 OS 권한) */
  async requestPermission() {
    if (typeof Notification === 'undefined') {
      return 'unsupported';
    }
    if (Notification.permission === 'default') {
      try {
        return await Notification.requestPermission();
      } catch {
        return Notification.permission;
      }
    }
    return Notification.permission;
  },
  /**
   * 단일 사용자에게 알림 발송 — 운영자/사장 전용 broadcast 엔드포인트가 추후 PR에서 정식화 예정.
   * 지금은 stub: 콘솔 로그 + resolved promise.
   */
  async sendNotification(userId, payload) {
    console.info('[push:stub] sendNotification', { userId, payload });
    return { success: true, stub: true, recipient: userId };
  },
  async sendBulkNotification(userIds = [], payload) {
    console.info('[push:stub] sendBulkNotification', { count: userIds.length, payload });
    return { success: true, stub: true, count: userIds.length };
  },
};

export default PushService;
