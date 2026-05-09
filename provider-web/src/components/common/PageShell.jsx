import { useEffect } from 'react';
import './PageShell.css';

/**
 * PageShell — 페이지 wrapper.
 *
 *  - theme="provider" | "admin"
 *    <html data-theme="…"> 에 attribute 를 적용하여
 *    accent / 배경 그라데이션을 토큰 단에서 전환합니다.
 *  - title / subtitle (optional) — 페이지 타이틀 영역.
 *  - actions (optional) — 타이틀 우측 영역 (검색 버튼 등).
 *  - max="default" | "narrow" | "wide"
 *
 * 향후 Dashboard / Facilities / Stamps 등 다른 페이지도 PageShell 로 통일하면
 * 페이지마다 다른 배경/여백 문제를 한 곳에서 통제 가능.
 */
export default function PageShell({
  theme = 'provider',
  title,
  subtitle,
  actions,
  max = 'default',
  className = '',
  children,
}) {
  // theme attribute 를 <html> 에 적용 — 토큰 스코프가 글로벌하게 풀림.
  useEffect(() => {
    const root = document.documentElement;
    const prev = root.getAttribute('data-theme');
    root.setAttribute('data-theme', theme);
    return () => {
      if (prev === null) root.removeAttribute('data-theme');
      else root.setAttribute('data-theme', prev);
    };
  }, [theme]);

  return (
    <div className={['pw-page', `pw-page--${max}`, className].filter(Boolean).join(' ')}>
      {(title || actions) && (
        <header className="pw-page-header">
          <div className="pw-page-header-text">
            {title && <h1 className="pw-page-title">{title}</h1>}
            {subtitle && <p className="pw-page-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="pw-page-actions">{actions}</div>}
        </header>
      )}
      {children}
    </div>
  );
}
