import { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import './GroupCard.css';

/**
 * GroupCard — 다건 신청 묶음 헤더 + 자식 카드 컨테이너.
 *
 * 디자인 가이드 v1.0 정렬:
 *   - 헤더: 좌측 아바타 + 신청번호/결제완료 pill + subtitle + 우측 chevron
 *   - 진행률 chip 제거 (정보 hierarchy 단순화 — child 카드의 status badge 로 충분)
 *   - 헤더 클릭으로 자식 카드 collapse / expand
 *
 * props:
 *   leading             — 헤더 좌측 슬롯. <CardAvatar> 권장.
 *   groupId             — 신청번호 (예: PW-20260509-001)
 *   paid                — true 면 "결제완료" pill 노출
 *   subtitle            — 헤더 아래 한 줄 부가 정보
 *   defaultCollapsed    — 처음에 접힌 상태로 시작 (default false = 펼친 상태)
 *   collapsible         — 접기/펼치기 가능 여부 (default true)
 *   children
 */
export default function GroupCard({
  leading,
  groupId,
  paid = false,
  subtitle,
  defaultCollapsed = false,
  collapsible = true,
  children,
  className = '',
}) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  const handleToggle = () => {
    if (!collapsible) return;
    setCollapsed((c) => !c);
  };

  const Chevron = collapsed ? ChevronDown : ChevronUp;

  return (
    <section className={`pw-group ${className}`}>
      <header
        className={`pw-group-header ${collapsible ? 'is-collapsible' : ''}`}
        onClick={collapsible ? handleToggle : undefined}
        role={collapsible ? 'button' : undefined}
        tabIndex={collapsible ? 0 : undefined}
        aria-expanded={collapsible ? !collapsed : undefined}
        onKeyDown={collapsible ? (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleToggle();
          }
        } : undefined}
      >
        {leading && <span className="pw-group-leading">{leading}</span>}
        <div className="pw-group-head-text">
          <div className="pw-group-meta">
            <span className="pw-group-id">{groupId}</span>
            {paid && <span className="pw-group-paid">결제완료</span>}
          </div>
          {subtitle && (
            <span className="pw-group-subtitle">{subtitle}</span>
          )}
        </div>
        {collapsible && (
          <Chevron size={20} className="pw-group-chevron" aria-hidden="true" />
        )}
      </header>
      {!collapsed && (
        <div className="pw-group-children">
          {children}
        </div>
      )}
    </section>
  );
}
