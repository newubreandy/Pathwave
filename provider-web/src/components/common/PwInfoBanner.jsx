/**
 * PwInfoBanner — 공용 안내/경고 박스 (2026-05-27).
 *
 * variant
 * -------
 * - info    : 일반 안내 (회색 톤, ⓘ)
 * - warn    : 주의 (노란 톤, ⚠)
 * - danger  : 위험 (빨간 톤, ⚠)
 * - success : 성공 (녹색 톤, ✓)
 *
 * 사용
 * ----
 *   <PwInfoBanner variant="info">
 *     매장 정보 변경은 슈퍼어드민 승인 후 반영됩니다.
 *   </PwInfoBanner>
 *
 *   <PwInfoBanner variant="warn" icon={AlertTriangle}>
 *     가격은 원화(KRW)만 사용. 외국 통화는 자동 거부됩니다.
 *   </PwInfoBanner>
 */
import React from 'react';
import { Info, AlertTriangle, AlertOctagon, CheckCircle2 } from 'lucide-react';
import './PwInfoBanner.css';

const DEFAULT_ICONS = {
  info:    Info,
  warn:    AlertTriangle,
  danger:  AlertOctagon,
  success: CheckCircle2,
};

export default function PwInfoBanner({
  variant = 'info',
  icon: CustomIcon,
  children,
}) {
  const Icon = CustomIcon || DEFAULT_ICONS[variant] || Info;
  return (
    <div className={`pw-info-banner pw-info-banner--${variant}`} role="note">
      <span className="pw-info-banner__icon" aria-hidden="true">
        <Icon size={16} />
      </span>
      <div className="pw-info-banner__body">{children}</div>
    </div>
  );
}
