/**
 * StampService — 스탬프 카드/적립 백엔드 연동.
 *
 * 백엔드: routes/stamp.py — /api/stamps/*
 *   GET    /api/stamps                — 시설별 스탬프 카드 목록
 *   POST   /api/stamps                — 스탬프 카드 생성
 *   PATCH  /api/stamps/<id>           — 스탬프 카드 수정 (상태/혜택)
 *   DELETE /api/stamps/<id>           — 스탬프 카드 삭제
 *   POST   /api/stamps/grant          — 직접 스탬프 적립 (직원 카운터)
 *   GET    /api/stamps/<id>/history   — 적립 이력
 */
import apiClient from '../apiClient';

const StampService = {
  /** 매장별 스탬프 카드 목록 */
  list(facilityId) {
    const q = facilityId ? `?facility_id=${encodeURIComponent(facilityId)}` : '';
    return apiClient.get(`/api/stamps${q}`);
  },

  /**
   * 스탬프 카드 생성.
   * @param {Object} payload — { facility_id, title, benefit, target_count, expires_at, ... }
   */
  create(payload) {
    return apiClient.post('/api/stamps', payload);
  },

  /** 스탬프 카드 수정 */
  update(stampId, payload) {
    return apiClient.patch(`/api/stamps/${stampId}`, payload);
  },

  /** 스탬프 카드 삭제 */
  remove(stampId) {
    return apiClient.delete(`/api/stamps/${stampId}`);
  },

  /**
   * 직원이 매장 카운터에서 직접 스탬프 적립.
   * @param {Object} payload — { user_id, facility_id, stamp_card_id }
   */
  grant(payload) {
    return apiClient.post('/api/stamps/grant', payload);
  },

  /** 적립 이력 */
  history(stampId) {
    return apiClient.get(`/api/stamps/${stampId}/history`);
  },

  // ── 레거시 호환 shim (페이지 코드 변경 최소화) ────────────────────────────
  /** Stamps.jsx 호환: 백엔드 list() → stamp 배열 추출 */
  async getStamps() {
    try {
      const res = await this.list();
      return res?.stamps || res?.items || [];
    } catch (err) {
      if (err.status === 404 || err.unauthorized) return [];
      throw err;
    }
  },
  toggleStampStatus(stampId) {
    return this.update(stampId, { toggle_status: true });
  },
  deleteStamp(stampId) {
    return this.remove(stampId);
  },
};

export default StampService;
