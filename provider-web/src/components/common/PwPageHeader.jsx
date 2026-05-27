/**
 * PwPageHeader — 공용 페이지 헤더 (2026-05-27).
 *
 * 모든 페이지의 제목 + 부제 + 액션 영역 통일.
 *
 * props
 * -----
 * - icon       : lucide 컴포넌트 (선택)
 * - title      : 페이지 제목 (h1)
 * - subtitle   : 부제 (선택, 페이지 안내)
 * - actions    : 우측 버튼 영역 (선택)
 *
 * 사용
 * ----
 *   <PwPageHeader
 *     icon={Stamp}
 *     title="매장 메뉴 관리"
 *     subtitle="메뉴판 사진을 업로드하면 자동으로 항목이 추출됩니다."
 *     actions={<button className="pw-btn">새로고침</button>}
 *   />
 */
import React from 'react';
import './PwPageHeader.css';

export default function PwPageHeader({ icon: Icon, title, subtitle, actions }) {
  return (
    <header className="pw-page-header">
      <div className="pw-page-header__main">
        <h1 className="pw-page-header__title">
          {Icon && (
            <span className="pw-page-header__icon" aria-hidden="true">
              <Icon size={20} />
            </span>
          )}
          <span>{title}</span>
        </h1>
        {subtitle && (
          <p className="pw-page-header__subtitle">{subtitle}</p>
        )}
      </div>
      {actions && (
        <div className="pw-page-header__actions">
          {actions}
        </div>
      )}
    </header>
  );
}
