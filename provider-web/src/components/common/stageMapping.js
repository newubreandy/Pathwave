/**
 * stageMapping — applicationStatus → 4단계 스테퍼 번호 매핑.
 * 사장님 콘솔 정책 (PROVIDER_STATUS_GROUPS 와 정렬).
 *
 *   submitted / receiving                         → 1 (신청완료)
 *   beacon_setting / shipping_ready / service_ready → 2 (준비중)
 *   shipping                                      → 3 (배송중)
 *   delivered / active                            → 4 (배송완료)
 *   paused / terminated                            → 0 (스테퍼 비노출)
 *
 * 별도 파일로 분리한 이유:
 *   StageProgress.jsx 가 Fast-Refresh 호환되도록 컴포넌트 export 만 갖게.
 */

export const STAGE_LABELS = ['신청완료', '준비중', '배송중', '배송완료'];

export function getStageNumber(status) {
  if (['submitted', 'receiving'].includes(status)) return 1;
  if (['beacon_setting', 'shipping_ready', 'service_ready'].includes(status)) return 2;
  if (status === 'shipping') return 3;
  if (['delivered', 'active'].includes(status)) return 4;
  return 0;
}
