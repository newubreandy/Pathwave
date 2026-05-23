import apiClient from './apiClient.js';

function qs(params = {}) {
  const q = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ''))
  ).toString();
  return q ? '?' + q : '';
}

/**
 * P11 — 알림 부가서비스 어드민 워크플로 API 래퍼.
 *
 * 백엔드 라우트(routes/notification.py):
 *   GET    /api/admin/notifications                    큐 + 필터
 *   GET    /api/admin/notifications/<nid>              상세 + recipients_preview
 *   POST   /api/admin/notifications/<nid>/approve      review/unpaid → pending
 *   POST   /api/admin/notifications/<nid>/reject       → canceled
 *   POST   /api/admin/notifications/<nid>/dispatch     즉시 발송 + quota 차감
 *   GET    /api/admin/notifications/blocklist          금칙어 목록
 *   POST   /api/admin/notifications/blocklist          추가
 *   DELETE /api/admin/notifications/blocklist/<bid>    삭제
 */
export const notificationApi = {
  // ── 알림 큐 ────────────────────────────────────────────────
  loadQueue: (params = {}) =>
    apiClient.get(`/api/admin/notifications${qs(params)}`),

  getNotification: (nid) =>
    apiClient.get(`/api/admin/notifications/${nid}`),

  approve: (nid) =>
    apiClient.post(`/api/admin/notifications/${nid}/approve`),

  reject: (nid) =>
    apiClient.post(`/api/admin/notifications/${nid}/reject`),

  dispatch: (nid) =>
    apiClient.post(`/api/admin/notifications/${nid}/dispatch`),

  // ── 금칙어 ─────────────────────────────────────────────────
  loadBlocklist: () =>
    apiClient.get('/api/admin/notifications/blocklist'),

  addBlocklist: ({ term, severity, note }) =>
    apiClient.post('/api/admin/notifications/blocklist', { term, severity, note }),

  deleteBlocklist: (bid) =>
    apiClient.delete(`/api/admin/notifications/blocklist/${bid}`),
};

export default notificationApi;
