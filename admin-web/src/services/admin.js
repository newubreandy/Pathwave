import apiClient from './apiClient.js';

export const adminApi = {
  // 본인 (A-024 / A-023)
  me: () => apiClient.get('/api/admin/me'),
  changeMyPassword: (currentPassword, newPassword) =>
    apiClient.post('/api/admin/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
  systemHealth: () => apiClient.get('/api/admin/system/health'),

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

  // 약관/정책 관리 (PR #46)
  listPolicies: (lang = 'ko') =>
    apiClient.get(`/api/admin/policies?lang=${lang}`),
  listPolicyVersions: (kind, lang = 'ko') =>
    apiClient.get(`/api/policies/${kind}/versions?lang=${lang}`),
  getPolicyVersion: (kind, pid) =>
    apiClient.get(`/api/policies/${kind}/versions/${pid}`),
  getActivePolicy: (kind, lang = 'ko') =>
    apiClient.get(`/api/policies/${kind}?lang=${lang}`),
  createPolicy: (payload) =>
    apiClient.post('/api/admin/policies', payload),
  // C-2-4b — ko + en 동시 등록 (한 트랜잭션, 같은 버전·effective_at).
  // payload: {kind, version, effective_at, ko:{title?,body,change_log?}, en:{title?,body,change_log?}}
  createPolicyMultilang: (payload) =>
    apiClient.post('/api/admin/policies/multilang', payload),
  updatePolicy: (pid, payload) =>
    apiClient.patch(`/api/admin/policies/${pid}`, payload),
  deletePolicy: (pid) =>
    apiClient.delete(`/api/admin/policies/${pid}`),
  notifyPolicy: (pid, subType = 'all') =>
    apiClient.post(`/api/admin/policies/${pid}/notify`, { sub_type: subType }),

  // 앱 버전 강제 업데이트 (B/PR #180)
  // platform = 'ios' | 'android'
  // payload  = { min_supported, latest, store_url?, force_message? }
  listAppVersions: () => apiClient.get('/api/admin/app-versions'),
  upsertAppVersion: (platform, payload) =>
    apiClient.put(`/api/admin/app-versions/${platform}`, payload),
};

export default adminApi;
