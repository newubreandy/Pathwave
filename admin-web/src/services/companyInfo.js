/**
 * Phase M — 법인 정보 (footer 자동 동기).
 *
 * 백엔드:
 *   GET  /api/company-info                — 공개 (모든 콘솔 footer 가 사용)
 *   PUT  /api/admin/company-info          — 슈퍼어드민 upsert
 */
import apiClient from './apiClient.js';

export const companyInfoApi = {
  /** 현재 법인 정보 (값 없으면 모든 필드 null). */
  get() {
    return apiClient.get('/api/company-info');
  },

  /**
   * 일부 또는 전체 필드 upsert. 빈 문자열은 백엔드에서 null 로 저장됨.
   * @param {Partial<{
   *   company_name: string, ceo: string, biz_number: string,
   *   commerce_number: string, address: string, phone: string,
   *   email: string, hosting: string,
   * }>} payload
   */
  put(payload) {
    return apiClient.put('/api/admin/company-info', payload);
  },
};

export default companyInfoApi;
