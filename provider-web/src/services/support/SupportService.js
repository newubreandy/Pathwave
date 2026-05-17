/**
 * SupportService — 시설관리자 고객센터 + FAQ 백엔드 연동.
 *
 * 백엔드 (Phase I, sub_type='facility' 토큰):
 *   POST /api/support/tickets               — 본인 문의 작성
 *   GET  /api/support/tickets/me            — 본인 문의 목록
 *   GET  /api/support/tickets/me/<tid>      — 문의 상세 (ticket + messages)
 *   POST /api/support/tickets/me/<tid>/messages — 추가 메시지
 *   GET  /api/faqs?kind=provider&lang=ko    — 공개 FAQ
 */
import apiClient from '../apiClient';

const SupportService = {
  /** 본인 문의 작성 */
  createTicket({ subject, body, category }) {
    return apiClient.post('/api/support/tickets', { subject, body, category });
  },

  /** 본인 문의 목록 */
  listMyTickets() {
    return apiClient.get('/api/support/tickets/me');
  },

  /** 문의 상세 (ticket + messages thread) */
  getTicket(tid) {
    return apiClient.get(`/api/support/tickets/me/${tid}`);
  },

  /** 추가 메시지 전송 */
  addMessage(tid, body) {
    return apiClient.post(`/api/support/tickets/me/${tid}/messages`, { body });
  },

  /** 공개 FAQ (B2B provider 카테고리) */
  listFaqs() {
    return apiClient.get('/api/faqs?kind=provider&lang=ko');
  },
};

export default SupportService;
