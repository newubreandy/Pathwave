import apiClient from './apiClient.js';

function qs(params = {}) {
  const q = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ''))
  ).toString();
  return q ? '?' + q : '';
}

export const supportApi = {
  // ── 티켓 ────────────────────────────────────────────────────
  loadTickets: (params = {}) =>
    apiClient.get(`/api/admin/support/tickets${qs(params)}`),
  getTicket: (tid) =>
    apiClient.get(`/api/admin/support/tickets/${tid}`),
  reply: (tid, body) =>
    apiClient.post(`/api/admin/support/tickets/${tid}/reply`, { body }),
  patchTicket: (tid, payload) =>
    apiClient.patch(`/api/admin/support/tickets/${tid}`, payload),
  loadStats: () =>
    apiClient.get('/api/admin/support/stats'),

  // ── FAQ ─────────────────────────────────────────────────────
  loadFaqs: (params = {}) =>
    apiClient.get(`/api/admin/faqs${qs(params)}`),
  addFaq: (payload) =>
    apiClient.post('/api/admin/faqs', payload),
  patchFaq: (fid, payload) =>
    apiClient.patch(`/api/admin/faqs/${fid}`, payload),
  deleteFaq: (fid) =>
    apiClient.delete(`/api/admin/faqs/${fid}`),

  // ── 신고 ────────────────────────────────────────────────────
  loadReports: (params = {}) =>
    apiClient.get(`/api/admin/abuse-reports${qs(params)}`),
  patchReport: (rid, payload) =>
    apiClient.patch(`/api/admin/abuse-reports/${rid}`, payload),
};

export default supportApi;
