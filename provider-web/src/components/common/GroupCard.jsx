import { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import './GroupCard.css';

/**
 * GroupCard — 그룹핑 컨테이너.
 *
 * variant:
 *   container (default) — RePlan 스타일.
 *     ┌─ outer card (surface-1) ─────────────┐
 *     │  [leading] Title    paid     ChevUp  │   ← header row (클릭 = collapse/expand)
 *     │  subtitle                            │
 *     │  ┌─ inset row (surface-2) ─────────┐ │
 *     │  │ child item                      │ │
 *     │  └─────────────────────────────────┘ │
 *     │  ┌─ inset row ─────────────────────┐ │
 *     │  │ child item                      │ │
 *     │  └─────────────────────────────────┘ │
 *     └─────────────────────────────────────┘
 *
 *   stacked — 외곽 카드 없이 자식 카드들이 따로 쌓이는 변형 (legacy / 단순 묶음).
 *
 * 자식 항목은 호출부에서 자유롭게 렌더 — `<GroupCardItem>` 사용 권장 (RePlan inset row).
 *
 * props:
 *   leading        — 헤더 좌측 슬롯 (CardAvatar 권장).
 *   title          — 그룹 제목 (예: "오늘", "신청 PW-...", "Tasks")
 *   paid           — true 면 "결제완료" 보조 라벨 노출.
 *   subtitle       — 헤더 아래 한 줄 부가 정보.
 *   defaultCollapsed
 *   collapsible    — default true.
 *   variant        — 'container' (default) | 'stacked'
 *   onHeaderClick  — 헤더 자체 클릭 핸들러 (collapsible 보다 우선).
 */
export default function GroupCard({
  leading,
  title,
  groupId,         // backward compat — title 미지정 시 사용
  paid = false,
  subtitle,
  defaultCollapsed = false,
  collapsible = true,
  variant = 'container',
  onHeaderClick,
  children,
  className = '',
}) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const headLabel = title ?? groupId;

  const handleToggle = () => {
    if (onHeaderClick) {
      onHeaderClick();
      return;
    }
    if (!collapsible) return;
    setCollapsed((c) => !c);
  };

  const interactive = !!onHeaderClick || collapsible;
  const Chevron = collapsed ? ChevronDown : ChevronUp;

  return (
    <section className={`pw-group pw-group--${variant} ${className}`}>
      <header
        className={`pw-group-head ${interactive ? 'is-interactive' : ''}`}
        onClick={interactive ? handleToggle : undefined}
        role={interactive ? 'button' : undefined}
        tabIndex={interactive ? 0 : undefined}
        aria-expanded={collapsible ? !collapsed : undefined}
        onKeyDown={interactive ? (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleToggle();
          }
        } : undefined}
      >
        {leading && <span className="pw-group-leading">{leading}</span>}
        <div className="pw-group-head-text">
          <div className="pw-group-meta">
            <span className="pw-group-title">{headLabel}</span>
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
        <div className="pw-group-body">
          {children}
        </div>
      )}
    </section>
  );
}

/**
 * GroupCardItem — 컨테이너 안 inset row.
 *
 * 단독 카드(GlassCard)보다 가벼운 row 스타일. 클릭 시 전체 row 가 인터랙티브.
 * children 으로 [avatar, content, optional right slot] 자유 구성.
 */
export function GroupCardItem({
  onClick,
  selected = false,
  className = '',
  children,
  ...rest
}) {
  const interactive = typeof onClick === 'function';
  return (
    <div
      className={[
        'pw-group-item',
        interactive ? 'is-interactive' : '',
        selected ? 'is-selected' : '',
        className,
      ].filter(Boolean).join(' ')}
      onClick={onClick}
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      onKeyDown={interactive ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(e);
        }
      } : undefined}
      {...rest}
    >
      {children}
    </div>
  );
}
