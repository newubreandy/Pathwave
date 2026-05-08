import React from 'react';
import { STATUS_META } from './StatusBadge';
import './StatusTimeline.css';

/**
 * 서비스 신청 카드의 상태 메시지 + 마지막 업데이트 시각.
 * 사용자 요구:
 *   - 메시지 길어질 경우 2줄까지 + ellipsis
 *   - 시간은 상대시간 X — 실제 날짜시간 표시
 *   - attention / danger 상태일 때 좌측 색 막대로 강조 (a11y 보강)
 *
 * @param status            현재 상태 enum (StatusBadge 와 동일)
 * @param statusMessage     상태 설명 문구 (관리자 메시지 등). 없으면 안내 placeholder
 * @param statusUpdatedAt   "YYYY.MM.DD HH:mm" 또는 ISO8601 (자동 변환)
 * @param compact           true 일 시 작은 톤 (리스트 카드용 기본값)
 */

// "YYYY.MM.DD HH:mm" 또는 ISO 모두 수용 → 항상 실제 날짜시간 문자열로 환산
const formatStatusDateTime = (s) => {
  if (!s) return '';
  if (/^\d{4}\.\d{2}\.\d{2}/.test(s)) return s; // 이미 KR 포맷
  try {
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return s;
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return s;
  }
};

const StatusTimeline = ({
  status,
  statusMessage,
  statusUpdatedAt,
  compact = true,
  className = '',
}) => {
  const meta = STATUS_META[status];
  const variant = meta?.variant || 'neutral';
  const formatted = formatStatusDateTime(statusUpdatedAt);

  const hasMessage = !!(statusMessage && statusMessage.trim());
  const isAttentionLike = variant === 'attention' || variant === 'danger';

  return (
    <div
      className={`pw-status-timeline pw-status-timeline--${variant} ${compact ? 'is-compact' : ''} ${className}`}
    >
      {hasMessage ? (
        <p
          className="pw-status-timeline__message"
          title={statusMessage}
          aria-live={isAttentionLike ? 'polite' : undefined}
        >
          {statusMessage}
        </p>
      ) : (
        <p className="pw-status-timeline__placeholder">상태 변경 메시지 없음</p>
      )}
      {formatted && (
        <span className="pw-status-timeline__time">
          최종 업데이트 · {formatted}
        </span>
      )}
    </div>
  );
};

export default StatusTimeline;
