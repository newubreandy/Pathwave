import React from 'react';
import './StatusBadge.css';

/**
 * 서비스 신청/운영 상태 공통 배지 컴포넌트
 *
 * 사용처: 와이파이 / 스탬프 / 쿠폰 / 알림 등 신청 후 리스트 카드.
 * 백엔드 status enum 과 동일한 키로 운용 (호환 별칭 포함).
 *
 * 두 모드:
 *   - mode="provider"  : 사장님 콘솔용. 12개 내부 enum → 6개 그룹 라벨로 단순 노출
 *                        (신청완료 / 준비중 / 배송중 / 서비스중 / 일시중지 / 해지)
 *   - mode="admin"     : 슈퍼어드민용. 세분 enum 라벨 그대로 노출
 *
 * Variant 결정 기준:
 *   - neutral   : 진행 전/종료 (작성중·해지)
 *   - info      : 진행 중 정상 흐름 (신청완료·준비중·배송중)
 *   - success   : 사용자 의미상 OK 단계 (서비스중·결제완료·설치완료·발송완료)
 *   - warning   : 사용자 액션 대기 / 일시중지 (결제대기·발송대기·일시중지)
 *   - attention : 사용자 즉시 액션 필요 (호환 fallback 만 유지, 신정책에선 미사용)
 *   - danger    : 부정 종결 (반려·결제실패) — 사장님 화면에선 비노출
 *
 * a11y: 색상 외에 라벨 텍스트가 항상 노출. attention/danger 는 dot+inset 으로 의미 중복 전달.
 *
 * @example
 *   <StatusBadge status="active" />               // → "서비스중" (provider 기본)
 *   <StatusBadge status="active" mode="admin" />  // → "사용중"
 *   <StatusBadge status="beacon_setting" />       // → "준비중"
 */

// ── 내부 세분 enum (백엔드/admin-web 용) ────────────────────────
// 정책: payment_failed / rejected / info_requested / ended 등은
// provider-web 리스트에 노출되지 않음. 내부 호환 fallback 만 유지.
export const STATUS_META = {
  draft:                { label: '작성중',          variant: 'neutral'   },

  // 결제 후 신청 흐름
  submitted:            { label: '신청완료',        variant: 'info'      },
  receiving:            { label: '접수확인중',      variant: 'info'      },

  // 비콘 / 배송
  beacon_setting:       { label: '비콘세팅중',      variant: 'info'      },
  shipping_ready:       { label: '배송준비중',      variant: 'info'      },
  shipping:             { label: '배송중',          variant: 'info'      },
  delivered:            { label: '배송완료',        variant: 'success'   },
  service_ready:        { label: '서비스준비중',    variant: 'info'      },

  // 운영
  active:               { label: '사용중',          variant: 'success'   },
  paused:               { label: '서비스일시중지',  variant: 'warning'   },

  // 종결
  terminated:           { label: '해지',           variant: 'neutral'   },

  // ── 호환 fallback (신정책에서는 미사용, 잔존 데이터 보호) ────
  applied:              { label: '신청완료',        variant: 'info'      },
  paid:                 { label: '신청완료',        variant: 'info'      },
  review:               { label: '접수확인중',      variant: 'info'      },
  under_review:         { label: '접수확인중',      variant: 'info'      },
  provisioning:         { label: '비콘세팅중',      variant: 'info'      },
  installation_pending: { label: '비콘세팅중',      variant: 'info'      },
  installed:            { label: '배송완료',        variant: 'success'   },
  ended:                { label: '해지',           variant: 'neutral'   },

  // 사장님 화면에는 노출 X — 내부 fallback / admin-web 전용
  payment_failed:       { label: '결제실패',        variant: 'danger'    },
  info_requested:       { label: '확인 필요',       variant: 'attention' },
  rejected:             { label: '반려',           variant: 'danger'    },

  // 알림 전용 (와이파이 무관, 후속 PR 활용)
  send_pending:         { label: '발송대기',        variant: 'warning'   },
  sent:                 { label: '발송완료',        variant: 'success'   },
};

// ── 사장님 콘솔용 그룹 ─────────────────────────────────────────
// PROVIDER_STATUS_GROUPS — 그룹 라벨/variant 정의 + 그룹 카운트 표시 순서
//
// 정책 매핑 (사용자 요구 2026-05-09 update):
//   submitted / receiving                                → 신청접수      (신청 진행중 탭)
//   beacon_setting / shipping_ready / service_ready      → 준비중        (신청 진행중 탭)
//   shipping                                             → 배송중        (신청 진행중 탭)
//   delivered / installed                                → 서비스대기    ★ 운영중 탭 (이전 진행중)
//   active                                               → 서비스중      (운영중 탭)
//   paused                                               → 일시중지      (운영중 탭 최하단)
//   terminated                                           → 해지          (운영중 탭 최하단)
//
// 변경 의도:
//   "신청완료" 라벨이 "끝났다" 로 오해됨 → "신청접수" 로 명확화.
//   배송완료(delivered) = 신청 단계 끝 → 운영중 탭으로 이동, 라벨 "서비스대기".
//   사용자 활성화(active 토글) 전까지 서비스대기 상태로 운영중 탭에 노출.
export const PROVIDER_STATUS_GROUPS = {
  applied:        { label: '신청접수', variant: 'info',    keys: ['submitted', 'receiving', 'applied', 'paid', 'review', 'under_review'] },
  preparing:      { label: '준비중',   variant: 'info',    keys: ['beacon_setting', 'shipping_ready', 'service_ready', 'provisioning', 'installation_pending'] },
  shipping:       { label: '배송중',   variant: 'info',    keys: ['shipping'] },
  serviceWaiting: { label: '서비스대기', variant: 'info',  keys: ['delivered', 'installed'] },
  live:           { label: '서비스중', variant: 'success', keys: ['active'] },
  paused:         { label: '일시중지', variant: 'warning', keys: ['paused'] },
  terminated:     { label: '해지',     variant: 'neutral', keys: ['terminated', 'ended'] },
};

// ── 섹션 (탭) ─────────────────────────────────────────────────
// 사장님 콘솔 탭 구조 (사용자 요구 2026-05-09 정리):
//   inProgress = 신청접수 + 준비중 + 배송중  (배송완료 제외)
//   live       = 서비스대기 + 서비스중 + 일시중지 + 해지 (운영중 탭 = 신청 끝난 모든 항목)
//
// paused / terminated 키는 운영중 렌더 정렬용으로 별도 보존 (탭 자체는 분리되지 않음).
export const PROVIDER_SECTIONS = {
  inProgress: { label: '신청 진행중',   groups: ['applied', 'preparing', 'shipping'] },
  live:       { label: '운영중',        groups: ['serviceWaiting', 'live'] },
  paused:     { label: '일시중지',      groups: ['paused'] },
  terminated: { label: '해지',          groups: ['terminated'] },
};

// status enum → 섹션 key (inProgress/live/paused/terminated)
export const getProviderSection = (status) => {
  const groupKey = getProviderGroup(status);
  if (!groupKey) return null;
  for (const [sectionKey, def] of Object.entries(PROVIDER_SECTIONS)) {
    if (def.groups.includes(groupKey)) return sectionKey;
  }
  return null;
};

// 사장님 콘솔에서 리스트/카운트 자체에서 비노출할 status 키
//   결제실패는 PG 단계에서 처리 → 신청 리스트에 들어오지 않음 (정책)
export const PROVIDER_HIDDEN_STATUSES = new Set([
  'draft',           // 미저장/미결제 = 신청 자체 미생성
  'payment_failed',  // PG 단계 처리 → 리스트 비노출
  'info_requested',  // 신정책 미사용 (호환 fallback 데이터만 안전 처리)
  'rejected',        // 신정책 미사용
]);

// status (세분 enum) → 그룹 key
export const getProviderGroup = (status) => {
  for (const [groupKey, meta] of Object.entries(PROVIDER_STATUS_GROUPS)) {
    if (meta.keys.includes(status)) return groupKey;
  }
  return null;
};

// status → 사장님 콘솔에서 보여줄 라벨/variant (그룹 매핑 + fallback)
export const getProviderStatusMeta = (status) => {
  const groupKey = getProviderGroup(status);
  if (groupKey) {
    return PROVIDER_STATUS_GROUPS[groupKey];
  }
  // 그룹 매핑 실패: STATUS_META 폴백 (라벨/variant 보존)
  return STATUS_META[status] || null;
};

const StatusBadge = ({
  status,
  label,
  size = 'md',           // 'sm' | 'md' | 'lg'
  mode = 'provider',     // 'provider' | 'admin'
  className = '',
  title,
}) => {
  if (!status) return null;

  const meta = mode === 'provider'
    ? getProviderStatusMeta(status)
    : STATUS_META[status];

  const variant = meta?.variant || 'neutral';
  const text = label || meta?.label || status;
  const needsDot = variant === 'attention' || variant === 'danger';

  return (
    <span
      className={`pw-status-badge pw-status-${variant} pw-status-${size} ${needsDot ? 'has-dot' : ''} ${className}`}
      title={title || text}
      role="status"
      aria-label={text}
    >
      {needsDot && <span className="pw-status-dot" aria-hidden="true" />}
      {text}
    </span>
  );
};

export default StatusBadge;
