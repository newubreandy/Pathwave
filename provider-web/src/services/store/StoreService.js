/**
 * StoreService — 시설(매장) CRUD 백엔드 연동.
 *
 * 백엔드: routes/store.py — /api/facilities/*
 *   GET    /api/facilities                   — 내 매장 목록
 *   GET    /api/facilities/<fid>             — 매장 상세
 *   POST   /api/facilities                   — 매장 생성
 *   PATCH  /api/facilities/<fid>             — 매장 정보 수정
 *   DELETE /api/facilities/<fid>             — 매장 삭제
 *   POST   /api/facilities/<fid>/claim-beacon — 비콘 SN 클레임
 */
import apiClient from '../apiClient';

const StoreService = {
  /** 내 매장 목록 */
  list() {
    return apiClient.get('/api/facilities');
  },

  /** 매장 상세 */
  get(fid) {
    return apiClient.get(`/api/facilities/${fid}`);
  },

  /**
   * 매장 생성.
   * @param {Object} payload — { name, category, address, phone, business_hours, description, ... }
   */
  create(payload) {
    return apiClient.post('/api/facilities', payload);
  },

  /** 매장 정보 수정 */
  update(fid, payload) {
    return apiClient.patch(`/api/facilities/${fid}`, payload);
  },

  /** 매장 삭제 */
  remove(fid) {
    return apiClient.delete(`/api/facilities/${fid}`);
  },

  /** 비콘 SN 클레임 — 운영자가 발급한 비콘 시리얼을 본인 매장에 연결 */
  claimBeacon(fid, beaconSn) {
    return apiClient.post(`/api/facilities/${fid}/claim-beacon`, { sn: beaconSn });
  },
};

export default StoreService;
