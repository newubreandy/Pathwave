import apiClient from './apiClient.js';

/**
 * i18n 관리 API 서비스.
 * GET  /api/admin/i18n
 * POST /api/admin/i18n/translate
 * POST /api/admin/i18n/:key/:lang
 * GET  /api/admin/i18n/missing/:lang
 */

export const i18nApi = {
  /** 전체 번역 그리드 로드 */
  loadGrid: () => apiClient.get('/api/admin/i18n'),

  /** 22개 언어 자동 번역 */
  autoTranslate: ({ key, ko, onlyMissing = false, sourceLang } = {}) =>
    apiClient.post('/api/admin/i18n/translate', {
      key,
      ko,
      ...(sourceLang ? { source_lang: sourceLang } : {}),
      only_missing: onlyMissing,
    }),

  /** 단일 키/언어 수동 upsert */
  upsert: (key, lang, value, verified = false) =>
    apiClient.post(`/api/admin/i18n/${encodeURIComponent(key)}/${lang}`, { value, verified }),

  /** 미번역 키 목록 */
  loadMissing: (lang) => apiClient.get(`/api/admin/i18n/missing/${lang}`),
};

export default i18nApi;
