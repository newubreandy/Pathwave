import React from 'react';
import './StatusBadge.css';

/**
 * 서비스 신청/운영 상태 공통 배지 컴포넌트
 *
 * 사용처: 와이파이 / 스탬프 / 쿠폰 / 알림 등 신청 후 리스트 카드
 * 공통 status enum 을 백엔드와 동일한 키로 운용해 라벨/색상 일관 유지.
 *
 * @example
 *   <StatusBadge status="active" />          // → "사용중" (success)
 *   <StatusBadge status="payment_pending" /> // → "결제대기" (warning)
 *   <StatusBadge status="active" label="진행중" /> // 라벨 override
 */

// 공통 status 사전 — 백엔드 enum 과 1:1 매핑
//   variant: neutral | info | success | warning | danger
//   tone   : 디자인 토큰 기반 (--pw-badge-*, --pw-success/error/warning/primary-light)
export const STATUS_META = {
  draft:           { label: '작성중',   variant: 'neutral' },
  applied:         { label: '신청완료', variant: 'info'    },
  review:          { label: '검토중',   variant: 'info'    },
  payment_pending: { label: '결제대기', variant: 'warning' },
  paid:            { label: '결제완료', variant: 'success' },
  provisioning:    { label: '적용대기', variant: 'info'    },
  active:          { label: '사용중',   variant: 'success' },
  send_pending:    { label: '발송대기', variant: 'warning' },
  sent:            { label: '발송완료', variant: 'success' },
  rejected:        { label: '반려',     variant: 'danger'  },
  ended:           { label: '종료',     variant: 'neutral' },
  terminated:      { label: '해지',     variant: 'neutral' },
};

const StatusBadge = ({
  status,
  label,
  size = 'md',          // 'sm' | 'md' | 'lg'
  className = '',
  title,                // 툴팁용 (상태 설명 문구)
}) => {
  const meta = STATUS_META[status];
  if (!meta) {
    // 등록되지 않은 status 는 안전하게 neutral / 그대로 노출
    if (!status) return null;
    return (
      <span
        className={`pw-status-badge pw-status-neutral pw-status-${size} ${className}`}
        title={title}
      >
        {label || status}
      </span>
    );
  }
  return (
    <span
      className={`pw-status-badge pw-status-${meta.variant} pw-status-${size} ${className}`}
      title={title}
    >
      {label || meta.label}
    </span>
  );
};

export default StatusBadge;
