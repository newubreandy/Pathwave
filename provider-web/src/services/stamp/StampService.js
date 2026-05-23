/**
 * StampService — 스탬프 정책 + 적립 백엔드 연동.
 *
 * 백엔드: routes/stamp.py
 *   GET    /api/facilities/<fid>/stamp-policy    — 매장 스탬프 정책 조회
 *   PUT    /api/facilities/<fid>/stamp-policy    — 정책 upsert (등록/수정)
 *   DELETE /api/facilities/<fid>/stamp-policy    — 정책 비활성 (소프트 삭제)
 *
 *   POST   /api/facilities/<fid>/stamps          — 스탬프 적립 (1개 단위)
 *   GET    /api/facilities/<fid>/stamps          — 시설별 적립 목록
 *   PATCH  /api/stamps/<sid>                     — 적립 보정 (수량/note)
 *   DELETE /api/stamps/<sid>                     — 오적립 취소 (hard delete)
 *
 * 정책: 매장당 1개의 active 스탬프 정책. PUT 가 자동으로 기존 active → 신규 교체.
 *
 * ⚠ apiClient 는 응답 본문을 그대로 반환 — res.policy / res.stamps / res.stamp
 */
import apiClient from '../apiClient';

const StampService = {
  // ── 스탬프 정책 ─────────────────────────────────────────────────────────
  /** 매장 스탬프 정책 조회 (active 1개 또는 null) */
  getPolicy(facilityId) {
    return apiClient.get(`/api/facilities/${facilityId}/stamp-policy`);
  },

  /**
   * 스탬프 정책 등록/수정 (upsert).
   * @param {Object} payload — { reward_threshold, reward_description,
   *                             expires_days, design_image_url,
   *                             auto_stamp_enabled, auto_stamp_cooldown_minutes,
   *                             reward_coupon_title, reward_coupon_benefit,
   *                             reward_coupon_validity_days }
   */
  upsertPolicy(facilityId, payload) {
    return apiClient.put(`/api/facilities/${facilityId}/stamp-policy`, payload);
  },

  /** 스탬프 정책 비활성 (소프트 삭제 — 적립 기록은 유지) */
  deactivatePolicy(facilityId) {
    return apiClient.delete(`/api/facilities/${facilityId}/stamp-policy`);
  },

  // ── 스탬프 적립 ─────────────────────────────────────────────────────────
  /** 시설별 적립 목록 */
  listStamps(facilityId) {
    return apiClient.get(`/api/facilities/${facilityId}/stamps`);
  },

  /**
   * 직원 카운터에서 직접 스탬프 적립.
   * @param {Object} payload — { user_id, amount?, note? }
   */
  grantStamp(facilityId, payload) {
    return apiClient.post(`/api/facilities/${facilityId}/stamps`, payload);
  },

  /** 적립 보정 (수량/note) */
  updateStamp(stampId, payload) {
    return apiClient.patch(`/api/stamps/${stampId}`, payload);
  },

  /** 오적립 취소 (hard delete) */
  deleteStamp(stampId) {
    return apiClient.delete(`/api/stamps/${stampId}`);
  },
};

export default StampService;
