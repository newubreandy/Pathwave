/**
 * ReportService — 매장이 손님(회원)을 신고.
 *
 * 출시 심사 대비 (Apple App Store Guideline 1.2 — UGC 모더레이션):
 * 매장도 채팅에서 욕설·불법·스팸 등 이용규칙을 위반하는 손님을 신고할 수 있다.
 *
 * 백엔드: routes/abuse_report.py
 *   POST /api/abuse-reports  body {target_kind, target_id, reason_code, reason_detail?}
 * reporter_kind('facility')는 백엔드가 facility 토큰으로 자동 판별한다.
 */
import apiClient from './apiClient';

/** 백엔드 허용 reason_code (routes/abuse_report.py _ALLOWED_REASON) */
export const REPORT_REASONS = [
  { code: 'spam',          labelKey: 'chat.report_reason_spam',          labelDefault: '스팸·광고' },
  { code: 'abuse',         labelKey: 'chat.report_reason_abuse',         labelDefault: '욕설·혐오' },
  { code: 'illegal',       labelKey: 'chat.report_reason_illegal',       labelDefault: '불법 정보·사기' },
  { code: 'inappropriate', labelKey: 'chat.report_reason_inappropriate', labelDefault: '부적절한 콘텐츠' },
  { code: 'other',         labelKey: 'chat.report_reason_other',         labelDefault: '기타' },
];

const ReportService = {
  /**
   * 손님 신고.
   * @param {number} userId      신고 대상 손님 user_id
   * @param {string} reasonCode  REPORT_REASONS 의 code 중 하나
   * @param {string} [detail]    상세 사유 (선택)
   */
  reportUser(userId, reasonCode, detail) {
    const body = {
      target_kind: 'user',
      target_id: userId,
      reason_code: reasonCode,
    };
    if (detail && detail.trim()) body.reason_detail = detail.trim();
    return apiClient.post('/api/abuse-reports', body);
  },
};

export default ReportService;
