/**
 * CouponService — 쿠폰 발급/사용 백엔드 연동.
 *
 * 백엔드: routes/coupon.py
 *   POST   /api/facilities/<fid>/coupons  — 발급
 *   GET    /api/facilities/<fid>/coupons  — 매장 쿠폰 목록
 *   GET    /api/coupons/<cid>             — 단건 조회
 *   PATCH  /api/coupons/<cid>             — 수정 (title/benefit/expires_at)
 *   DELETE /api/coupons/<cid>             — 회수 (사용·만료 쿠폰만)
 *   POST   /api/coupons/<cid>/use         — 사용 처리 (직원이 카운터에서)
 */
import apiClient from '../apiClient';

const CouponService = {
  /** 매장 쿠폰 목록. ?user_id, ?status 필터 지원 */
  list(facilityId, { userId, status } = {}) {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (status) params.append('status', status);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`/api/facilities/${facilityId}/coupons${qs}`);
  },

  /**
   * 쿠폰 발급.
   * @param {number} facilityId
   * @param {Object} payload — { title, benefit?, expires_at?, user_id? | user_ids?: [...] }
   */
  issue(facilityId, payload) {
    return apiClient.post(`/api/facilities/${facilityId}/coupons`, payload);
  },

  /** 쿠폰 단건 조회 */
  get(couponId) {
    return apiClient.get(`/api/coupons/${couponId}`);
  },

  /** 쿠폰 수정 (title/benefit/expires_at). 사용 완료 쿠폰은 변경 불가. */
  update(couponId, payload) {
    return apiClient.patch(`/api/coupons/${couponId}`, payload);
  },

  /** 쿠폰 회수 (사용·만료 쿠폰만 가능). */
  remove(couponId) {
    return apiClient.delete(`/api/coupons/${couponId}`);
  },

  /** 사용 처리 (직원이 QR/번호로 처리). */
  use(couponId) {
    return apiClient.post(`/api/coupons/${couponId}/use`);
  },
};

export default CouponService;
