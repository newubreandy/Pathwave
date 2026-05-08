import React from 'react';
import './StatusBadge.css';

/**
 * 서비스 신청/운영 상태 공통 배지 컴포넌트
 *
 * 사용처: 와이파이 / 스탬프 / 쿠폰 / 알림 등 신청 후 리스트 카드.
 * 백엔드 status enum 과 동일한 키로 운용 (호환 별칭 포함).
 *
 * Variant 결정 기준:
 *   - neutral   : 진행 전/종료 (작성중·종료·해지)
 *   - info      : 진행 중 정상 흐름 (신청접수·검토·설치준비·결제완료·발송완료 등)
 *   - success   : 사용자 의미상 OK 단계 (사용중·결제완료·설치완료·발송완료)
 *   - warning   : 사용자 액션 대기 (결제대기·발송대기)
 *   - attention : 사용자 즉시 액션 필요 — 강조 (추가정보 요청)
 *   - danger    : 부정 종결 (반려)
 *
 * a11y: 색상 외에 라벨 텍스트가 항상 노출되어, 색맹/저시력 환경에서도 의미 전달.
 *       attention/danger 는 좌측 dot + inset border 로 추가 강조.
 *
 * @example
 *   <StatusBadge status="active" />
 *   <StatusBadge status="info_requested" />     // 강조 attention
 *   <StatusBadge status="rejected" />           // 강조 danger
 *   <StatusBadge status="active" label="진행중" /> // 라벨 override
 */

// 공통 status 사전 — 백엔드 enum 과 1:1 매핑
//   기존 키(applied/review/provisioning) 도 호환 유지: 동일 라벨/variant 로 매핑
export const STATUS_META = {
  // ── 진행 흐름 ─────────────────────────────────────────────
  draft:                { label: '작성중',        variant: 'neutral'   },

  // 신청접수 (제출 직후)
  applied:              { label: '신청접수',      variant: 'info'      }, // 호환 별칭
  submitted:            { label: '신청접수',      variant: 'info'      },

  // 관리자 검토중
  review:               { label: '관리자 검토중',  variant: 'info'      }, // 호환 별칭
  under_review:         { label: '관리자 검토중',  variant: 'info'      },

  // 사장님 액션 필요 — 강조
  info_requested:       { label: '추가정보 요청',  variant: 'attention' },

  // 결제 단계
  payment_pending:      { label: '결제대기',      variant: 'warning'   },
  paid:                 { label: '결제완료',      variant: 'success'   },

  // 설치 단계
  provisioning:         { label: '설치준비중',    variant: 'info'      }, // 호환 별칭
  installation_pending: { label: '설치준비중',    variant: 'info'      },
  installed:            { label: '설치완료',      variant: 'success'   },

  // 사용 단계
  active:               { label: '사용중',        variant: 'success'   },

  // 알림 전용
  send_pending:         { label: '발송대기',      variant: 'warning'   },
  sent:                 { label: '발송완료',      variant: 'success'   },

  // 종결
  rejected:             { label: '반려',         variant: 'danger'    },
  ended:                { label: '종료',         variant: 'neutral'   },
  terminated:           { label: '해지',         variant: 'neutral'   },
};

const StatusBadge = ({
  status,
  label,
  size = 'md',          // 'sm' | 'md' | 'lg'
  className = '',
  title,                // 툴팁용 (상태 설명 문구)
}) => {
  const meta = STATUS_META[status];
  if (!status) return null;

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
