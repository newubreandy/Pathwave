/**
 * Phase M — 법인 정보 (footer 자동 동기).
 *
 * 백엔드 (공개 GET — 사장님 콘솔에서도 footer 표시용):
 *   GET /api/company-info
 */
import apiClient from '../apiClient';

const CompanyInfoService = {
  /** 공개 GET — 슈퍼어드민이 입력한 법인 정보. */
  get() {
    return apiClient.get('/api/company-info');
  },
};

export default CompanyInfoService;
