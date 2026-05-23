/**
 * NotificationService — 알림 부가서비스 (사장 측) 백엔드 연동.
 *
 * 백엔드 (P11):
 *   GET    /api/facilities/<fid>/notifications/quota   잔여 quota 통계
 *   POST   /api/facilities/<fid>/notifications         알림 신청 (12h/quota/AI 검토)
 *   GET    /api/facilities/<fid>/notifications         발송 이력/예약
 *   GET    /api/facilities/<fid>/notifications/<nid>   상세
 *   DELETE /api/facilities/<fid>/notifications/<nid>   취소 (pending/review/unpaid)
 *
 * 1계정1매장 정책 — facilityId 는 호출자가 미리 받아 보관 (마운트 시 listFacilities).
 */
import apiClient from '../apiClient';

const NotificationService = {
  /** 내 매장 목록 — 첫 매장 id 를 facilityId 로 사용 (1계정1매장 정책). */
  loadMyFacilityId: async () => {
    const data = await apiClient.get('/api/facilities');
    const list = data.facilities || [];
    if (list.length === 0) return null;
    return list[0].id;
  },

  /** quota 잔량 통계 — {purchased, used, available, expired}. */
  loadQuota: (fid) =>
    apiClient.get(`/api/facilities/${fid}/notifications/quota`),

  /** 알림 신청. */
  createNotification: (fid, payload) =>
    apiClient.post(`/api/facilities/${fid}/notifications`, payload),

  /** 발송 이력/예약 알림 목록. */
  listNotifications: (fid) =>
    apiClient.get(`/api/facilities/${fid}/notifications`),

  /** 상세. */
  getNotification: (fid, nid) =>
    apiClient.get(`/api/facilities/${fid}/notifications/${nid}`),

  /** 취소 (pending/review/unpaid 만). */
  cancelNotification: (fid, nid) =>
    apiClient.delete(`/api/facilities/${fid}/notifications/${nid}`),
};

export default NotificationService;
