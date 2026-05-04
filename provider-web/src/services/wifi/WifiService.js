/**
 * WifiService — 매장 WiFi 프로파일 등록/조회 백엔드 연동.
 *
 * 백엔드: routes/beacon.py — /api/beacon/wifi
 *   POST /api/beacon/wifi  — WiFi 프로파일 저장 (서버측 AES-256-GCM 암호화)
 *
 * 비밀번호는 HTTPS로 평문 전송하며, 서버가 저장 시 강암호화한다.
 * 클라이언트는 절대 평문 비밀번호를 로컬에 저장하지 않는다.
 */
import apiClient from '../apiClient';

const WifiService = {
  /**
   * 매장 WiFi 프로파일 등록 / 갱신.
   * @param {Object} payload — { facility_id, ssid, password, security_type }
   */
  saveProfile(payload) {
    return apiClient.post('/api/beacon/wifi', payload);
  },

  /**
   * (편의) WiFi QR 코드 페이로드 생성 — 표준 포맷.
   * 클라이언트 사이드에서 QR 라이브러리에 직접 전달 가능.
   */
  buildQrPayload({ ssid, password, securityType = 'WPA' }) {
    const safe = (s) => (s || '').replace(/([\\;,:"])/g, '\\$1');
    return `WIFI:T:${securityType};S:${safe(ssid)};P:${safe(password)};;`;
  },
};

export default WifiService;
