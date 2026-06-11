/**
 * StampService — 스탬프 정책 백엔드 연동.
 *
 * 백엔드: routes/stamp.py
 *   GET    /api/facilities/<fid>/stamp-policy   — 현재 정책 조회
 *   PUT    /api/facilities/<fid>/stamp-policy   — 정책 upsert
 *   DELETE /api/facilities/<fid>/stamp-policy   — 정책 비활성 (적립 종료)
 *   GET    /api/facilities/<fid>/stamps         — 적립 내역
 */
import apiClient from '../apiClient';

/**
 * GET 응답의 policy 객체를 Stamps.jsx 카드 표시용으로 정규화.
 * @param {Object} policy — 백엔드 stamp-policy 원본
 * @returns {Object} 정규화된 스탬프 항목
 */
const normalizePolicy = (policy) => ({
  id: policy.id,
  name: policy.reward_description,
  threshold: policy.reward_threshold,
  expiresDays: policy.expires_days,
  autoStamp: !!policy.auto_stamp_enabled,
  cooldownMinutes: policy.auto_stamp_cooldown_minutes,
  status: 'active',
  period: policy.expires_days ? `적립일로부터 ${policy.expires_days}일` : '무기한',
  raw: policy,
});

const StampService = {
  /**
   * 매장 스탬프 정책 목록.
   * 정책이 없으면 [] 반환, 있으면 정규화된 항목 1개짜리 배열 반환.
   */
  async list(facilityId) {
    const res = await apiClient.get(`/api/facilities/${facilityId}/stamp-policy`);
    const policy = res?.policy ?? null;
    if (!policy) return [];
    return [normalizePolicy(policy)];
  },

  /** 정책 원본 조회 (StampForm edit/view 진입용). */
  get(facilityId) {
    return apiClient.get(`/api/facilities/${facilityId}/stamp-policy`);
  },

  /**
   * 정책 저장 (upsert).
   * @param {number|string} facilityId
   * @param {Object} payload — { reward_threshold, reward_description, expires_days?,
   *                             auto_stamp_enabled?, auto_stamp_cooldown_minutes? }
   */
  save(facilityId, payload) {
    return apiClient.put(`/api/facilities/${facilityId}/stamp-policy`, payload);
  },

  /**
   * 적립 종료 (비활성화, 기록 유지).
   */
  end(facilityId) {
    return apiClient.delete(`/api/facilities/${facilityId}/stamp-policy`);
  },

  /** 적립 내역 조회. */
  history(facilityId) {
    return apiClient.get(`/api/facilities/${facilityId}/stamps`);
  },
};

export default StampService;
