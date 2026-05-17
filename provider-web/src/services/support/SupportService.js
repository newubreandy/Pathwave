import apiClient from '../apiClient';

/**
 * SupportService — provider-web 의 고객센터/FAQ API 래퍼.
 *
 * - listFaqs / getCategories: 공개 GET (인증 불필요)
 * - createTicket / listMyTickets / getTicket / replyToTicket: 사장님 토큰 필요
 */
const SupportService = {
  listFaqs: async ({ category, lang = 'ko' } = {}) => {
    const params = new URLSearchParams({ kind: 'provider', lang });
    if (category) params.set('category', category);
    return apiClient.get(`/api/faqs?${params.toString()}`);
  },

  listCategories: async () =>
    apiClient.get('/api/support/categories?kind=provider'),

  createTicket: async ({ category, subject, body, priority = 'normal' }) =>
    apiClient.post('/api/support/tickets', { category, subject, body, priority }),

  listMyTickets: async () =>
    apiClient.get('/api/support/tickets/me'),

  getTicket: async (tid) =>
    apiClient.get(`/api/support/tickets/${tid}`),

  replyToTicket: async (tid, body) =>
    apiClient.post(`/api/support/tickets/${tid}/messages`, { body }),
};

export default SupportService;
