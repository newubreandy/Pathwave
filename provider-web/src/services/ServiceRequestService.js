/**
 * ServiceRequestService — 점주 서비스 신청 (비콘 프로비저닝 P-A, 2026-05-29).
 *
 * 백엔드: routes/service_request.py
 *   POST /api/service-requests   — 신청 생성 (units: 위치별 설치위치 + WiFi)
 *   GET  /api/service-requests   — 내 신청 목록
 *
 * 설계: docs/pathwave_beacon_provisioning_design_2026-05-29.md
 */
import apiClient from './apiClient';

const ServiceRequestService = {
  /**
   * 서비스 신청 생성.
   * @param {Object} p
   * @param {string} p.serviceType — 'wifi' | 'event' | 'notification' | 'stamp'
   * @param {string} [p.note]
   * @param {Array}  [p.wifiItems] — ServiceRequest 화면의 wifiItems (location/ssid/password/기간)
   */
  submit({ serviceType = 'wifi', note = '', wifiItems = [] }) {
    const units = (wifiItems || []).map((it) => ({
      location_label: it.installLocation ?? it.location ?? '',
      ssid:           it.wifiId ?? it.ssid ?? '',
      wifi_password:  it.wifiPassword ?? it.password ?? '',
      period_start:   it.startDate ?? '',
      period_end:     it.endDate ?? '',
    }));
    return apiClient.post('/api/service-requests', {
      service_type: serviceType,
      note,
      units,
    });
  },

  /** 내 신청 목록 */
  list() {
    return apiClient.get('/api/service-requests');
  },
};

export default ServiceRequestService;
