/**
 * NotificationPreferencesService — 알림 카테고리별 on/off (Phase L).
 *
 * 백엔드 (sub_type='facility' 토큰):
 *   GET  /api/facility/me/notification-preferences
 *   PUT  /api/facility/me/notification-preferences/{category}
 *
 * 사용자(mobile) 측은 /api/users/me/notification-preferences — 별도.
 */
import apiClient from '../apiClient';

const NotificationPreferencesService = {
  /** 카탈로그 + 현재 enabled 상태. */
  list() {
    return apiClient.get('/api/facility/me/notification-preferences');
  },

  /** 특정 카테고리 on/off. */
  set(category, enabled) {
    return apiClient.put(
      `/api/facility/me/notification-preferences/${encodeURIComponent(category)}`,
      { enabled },
    );
  },
};

export default NotificationPreferencesService;
