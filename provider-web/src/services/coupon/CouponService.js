/**
 * CouponService — 쿠폰 발급/사용 백엔드 연동.
 *
 * 백엔드: routes/coupon.py
 *   POST   /api/facilities/<fid>/coupons         — 시설에서 쿠폰 발급
 *   GET    /api/facilities/<fid>/coupons         — 시설별 발급 쿠폰 목록 (시설 측)
 *   GET    /api/coupons/<cid>                    — 쿠폰 단건 조회
 *   PATCH  /api/coupons/<cid>                    — 쿠폰 정보 수정 (만료일 등)
 *   DELETE /api/coupons/<cid>                    — 쿠폰 회수 (revoke)
 *   POST   /api/coupons/<cid>/use                — 쿠폰 사용 처리 (직원 카운터)
 *
 * ⚠ apiClient 는 응답 본문을 그대로 반환 — res.coupons / res.coupon
 */
import apiClient from '../apiClient';

const CouponService = {
  /**
   * 시설별 발급 쿠폰 목록.
   * @param {number|string} facilityId
   * @param {Object} [opts] — { status: 'active'|'used'|'expired'|'all' }
   */
  list(facilityId, { status } = {}) {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    const qs = params.toString();
    return apiClient.get(
      `/api/facilities/${facilityId}/coupons${qs ? `?${qs}` : ''}`
    );
  },

  /** 쿠폰 단건 조회 */
  get(couponId) {
    return apiClient.get(`/api/coupons/${couponId}`);
  },

  /**
   * 쿠폰 발급 (시설 → 사용자).
   * @param {number|string} facilityId
   * @param {Object} payload — { user_id, title, benefit, expires_at, ... }
   */
  issue(facilityId, payload) {
    return apiClient.post(`/api/facilities/${facilityId}/coupons`, payload);
  },

  /** 쿠폰 정보 수정 (만료일·혜택 등) */
  update(couponId, payload) {
    return apiClient.patch(`/api/coupons/${couponId}`, payload);
  },

  /** 쿠폰 회수 (revoke) */
  revoke(couponId) {
    return apiClient.delete(`/api/coupons/${couponId}`);
  },

  /** 쿠폰 사용 처리 — 직원 카운터에서 호출 */
  use(couponId) {
    return apiClient.post(`/api/coupons/${couponId}/use`, {});
  },
};

export default CouponService;
