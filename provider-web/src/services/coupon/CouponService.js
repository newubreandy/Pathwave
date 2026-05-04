/**
 * CouponService — 쿠폰 발급/사용 백엔드 연동.
 *
 * 백엔드: routes/coupon.py — /api/coupons/*
 *   GET    /api/coupons                — 시설별 쿠폰 목록
 *   POST   /api/coupons                — 쿠폰 정책 생성/발급
 *   PATCH  /api/coupons/<id>           — 쿠폰 정책 수정
 *   DELETE /api/coupons/<id>           — 쿠폰 정책 삭제
 *   POST   /api/coupons/redeem         — 쿠폰 사용 처리 (직원이 매장 카운터에서)
 *   GET    /api/coupons/<id>/redemptions — 사용 이력
 */
import apiClient from '../apiClient';

const CouponService = {
  /** 매장별 쿠폰 목록 */
  list(facilityId) {
    const q = facilityId ? `?facility_id=${encodeURIComponent(facilityId)}` : '';
    return apiClient.get(`/api/coupons${q}`);
  },

  /**
   * 쿠폰 정책/발급 생성.
   * @param {Object} payload — { facility_id, title, benefit, valid_from, valid_until, conditions, ... }
   */
  create(payload) {
    return apiClient.post('/api/coupons', payload);
  },

  /** 쿠폰 정책 수정 */
  update(couponId, payload) {
    return apiClient.patch(`/api/coupons/${couponId}`, payload);
  },

  /** 쿠폰 정책 삭제 */
  remove(couponId) {
    return apiClient.delete(`/api/coupons/${couponId}`);
  },

  /**
   * 쿠폰 사용 처리 (직원이 카운터에서 코드 입력 또는 스캔).
   * @param {Object} payload — { code }  또는  { coupon_id, user_id }
   */
  redeem(payload) {
    return apiClient.post('/api/coupons/redeem', payload);
  },

  /** 사용 이력 */
  redemptions(couponId) {
    return apiClient.get(`/api/coupons/${couponId}/redemptions`);
  },
};

export default CouponService;
