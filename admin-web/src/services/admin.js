import apiClient from './apiClient.js';

export const adminApi = {
  // 본인 (A-024 / A-023)
  me: () => apiClient.get('/api/admin/me'),
  // ── 금지어 (2026-06-09) ────────────────────────────────────────────
  listBannedWords: (q, kind) => {
    const qs = new URLSearchParams();
    if (q) qs.set('q', q);
    if (kind) qs.set('kind', kind);
    const s = qs.toString();
    return apiClient.get(`/api/admin/banned-words${s ? '?' + s : ''}`);
  },
  createBannedWord: (body) => apiClient.post('/api/admin/banned-words', body),
  updateBannedWord: (id, body) => apiClient.patch(`/api/admin/banned-words/${id}`, body),
  deleteBannedWord: (id) => apiClient.delete(`/api/admin/banned-words/${id}`),
  changeMyPassword: (currentPassword, newPassword) =>
    apiClient.post('/api/admin/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
  systemHealth: () => apiClient.get('/api/admin/system/health'),

  // 모니터링 (A-009/A-010/A-015 — D 번들2)
  adminListCoupons: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiClient.get(`/api/admin/coupons${q ? '?' + q : ''}`);
  },
  adminStaffReports: () => apiClient.get('/api/admin/staff/reports'),
  adminChatRooms: (limit = 100) =>
    apiClient.get(`/api/admin/chat/rooms?limit=${limit}`),

  // A-022 회원(사용자) 관리 (D 번들3-A)
  adminListUsers: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiClient.get(`/api/admin/users${q ? '?' + q : ''}`);
  },
  adminForceDeleteUser: (uid, reason = '') =>
    apiClient.post(`/api/admin/users/${uid}/force-delete`, { reason }),

  // 통계
  statsOverview: () => apiClient.get('/api/admin/stats/overview'),
  // 2026-06-12 — 처리 필요(액션) 현황. 대시보드 액션 보드용.
  statsPending: () => apiClient.get('/api/admin/stats/pending'),
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

  // 서비스 신청 ↔ 비콘 매칭 (P-B)
  listServiceRequests: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiClient.get(`/api/admin/service-requests${q ? '?' + q : ''}`);
  },
  matchRequestUnit: (unitId, beaconId) =>
    apiClient.post(`/api/admin/service-request-units/${unitId}/match`, { beacon_id: beaconId }),
  shipServiceRequest: (rid) =>
    apiClient.post(`/api/admin/service-requests/${rid}/ship`, {}),

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

  // 시즌 배경 테마 — 사용자 앱 글래스모피즘 BG (무재배포 운영)
  listThemes:    () => apiClient.get('/api/admin/themes'),
  createTheme:   (formData) => apiClient.postForm('/api/admin/themes', formData),
  updateTheme:   (tid, formData) =>
    apiClient.patchForm(`/api/admin/themes/${tid}`, formData),
  activateTheme: (tid) =>
    apiClient.post(`/api/admin/themes/${tid}/activate`, {}),
  deleteTheme:   (tid) => apiClient.delete(`/api/admin/themes/${tid}`),

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

  // D-4-pre 비용 모니터링 + 슈퍼어드민 알림
  costMonitor: (year, month) => {
    const q = new URLSearchParams();
    if (year)  q.set('year',  year);
    if (month) q.set('month', month);
    const s = q.toString();
    return apiClient.get(`/api/admin/cost-monitor${s ? '?' + s : ''}`);
  },
  criticalAlerts: () => apiClient.get('/api/admin/critical-alerts'),
  dismissAlert: (alertId, hours) =>
    apiClient.post(`/api/admin/alerts/${alertId}/dismiss`, { hours }),

  // Feature Flag (2026-06-08)
  listFeatures: () => apiClient.get('/api/admin/features'),
  setFeature:   (key, enabled) =>
    apiClient.patch(`/api/admin/features/${key}`, { enabled }),

  // 매장 업종 카테고리 (polish 작업)
  listCategories: () => apiClient.get('/api/admin/categories'),
  createCategory: (payload) => apiClient.post('/api/admin/categories', payload),
  updateCategory: (cid, payload) =>
    apiClient.patch(`/api/admin/categories/${cid}`, payload),
  deactivateCategory: (cid) => apiClient.delete(`/api/admin/categories/${cid}`),
  hardDeleteCategory: (cid) => apiClient.delete(`/api/admin/categories/${cid}?hard=1`),
};

export default adminApi;
