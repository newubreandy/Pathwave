import apiClient from './apiClient.js';

export const adminApi = {
  // 통계
  statsOverview: () => apiClient.get('/api/admin/stats/overview'),
  statsPayments: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiClient.get(`/api/admin/stats/payments${q ? '?' + q : ''}`);
  },

  // 비콘
  listBeacons: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiClient.get(`/api/admin/beacons${q ? '?' + q : ''}`);
  },
  importBeacons: (payload) => apiClient.post('/api/admin/beacons/import', payload),
  updateBeacon: (id, payload) => apiClient.patch(`/api/admin/beacons/${id}`, payload),
  assignBeacon: (id, facilityId) =>
    apiClient.post(`/api/admin/beacons/${id}/assign`, { facility_id: facilityId }),
  unassignBeacon: (id) => apiClient.post(`/api/admin/beacons/${id}/unassign`, {}),

  // 사장 가입 승인
  listFacilityAccounts: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiClient.get(`/api/admin/facility-accounts${q ? '?' + q : ''}`);
  },
  getFacilityAccount: (aid) => apiClient.get(`/api/admin/facility-accounts/${aid}`),
  verifyFacilityAccount: (aid, payload = {}) =>
    apiClient.post(`/api/admin/facility-accounts/${aid}/verify`, payload),
  suspendFacilityAccount: (aid, payload = {}) =>
    apiClient.post(`/api/admin/facility-accounts/${aid}/suspend`, payload),
  reactivateFacilityAccount: (aid) =>
    apiClient.post(`/api/admin/facility-accounts/${aid}/reactivate`, {}),

  // 결제·구독
  listPayments: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiClient.get(`/api/admin/payments${q ? '?' + q : ''}`);
  },
  refundPayment: (pid, payload = {}) =>
    apiClient.post(`/api/admin/payments/${pid}/refund`, payload),
  listSubscriptions: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiClient.get(`/api/admin/subscriptions${q ? '?' + q : ''}`);
  },

  // 배터리 모니터링 (PR #38)
  batteryStatus: (lowThreshold = 20) =>
    apiClient.get(`/api/admin/beacons/battery-status?low_threshold=${lowThreshold}`),
  batteryHistory: (bid, limit = 100) =>
    apiClient.get(`/api/admin/beacons/${bid}/battery-history?limit=${limit}`),

  // 시스템 공지 (PR #38)
  listAnnouncements: () => apiClient.get('/api/admin/announcements'),
  createAnnouncement: (payload) => apiClient.post('/api/admin/announcements', payload),
  updateAnnouncement: (aid, payload) =>
    apiClient.patch(`/api/admin/announcements/${aid}`, payload),
  deleteAnnouncement: (aid) => apiClient.delete(`/api/admin/announcements/${aid}`),
};

export default adminApi;
