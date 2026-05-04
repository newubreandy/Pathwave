import React, { useState, useEffect, useRef } from 'react';
import { Outlet, NavLink, Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Menu, X, ChevronLeft, ChevronRight, User, Settings } from 'lucide-react';
import './DashboardLayout.css';

const DashboardLayout = () => {
  const { t } = useTranslation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const [showLeftScroll, setShowLeftScroll] = useState(false);
  const [showRightScroll, setShowRightScroll] = useState(false);
  const navRef = useRef(null);

  const handleNavScroll = () => {
    if (navRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = navRef.current;
      setShowLeftScroll(scrollLeft > 0);
      setShowRightScroll(Math.ceil(scrollLeft + clientWidth) < scrollWidth);
    }
  };

  const scrollNav = (direction) => {
    if (navRef.current) {
      const scrollAmount = 150;
      navRef.current.scrollBy({ left: direction === 'left' ? -scrollAmount : scrollAmount, behavior: 'smooth' });
    }
  };

  useEffect(() => {
    handleNavScroll();
    window.addEventListener('resize', handleNavScroll);
    return () => window.removeEventListener('resize', handleNavScroll);
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);

    // 모바일 키보드 대응: Visual Viewport의 실제 높이를 CSS 변수로 전달
    const handleResize = () => {
      if (window.visualViewport) {
        document.documentElement.style.setProperty('--vh', `${window.visualViewport.height}px`);
      }
    };
    
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleResize);
      handleResize();
    }

    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleResize);
      }
    };
  }, []);

  // 전체 메뉴 항목 (오버레이 전체 메뉴용 — 설정 포함)
  const allNavItems = [
    { path: '/dashboard/chat', label: t('menu.chat', '채팅') },
    { path: '/dashboard/store', label: t('menu.store', '매장안내') },
    { path: '/dashboard/wifi', label: t('menu.wifi', '와이파이') },
    { path: '/dashboard/stamps', label: t('menu.stamps', '스탬프') },
    { path: '/dashboard/coupons', label: t('menu.coupons', '쿠폰') },
    { path: '/dashboard/notifications', label: t('menu.notifications', '알림발송') },
    { path: '/dashboard/report', label: t('menu.report', '리포트') },
    { path: '/dashboard/staff', label: t('menu.staff', '직원 관리') },
    { path: '/dashboard/payments', label: t('menu.payments', '결제관리') },
    { path: '/dashboard/settings', label: t('menu.settings', '설정') },
  ];

  // GNB 수평 메뉴 항목 (설정/직원관리 제외 — PC/모바일 모두 아이콘으로 접근)
  const gnbNavItems = allNavItems.filter(
    item => item.path !== '/dashboard/settings' && item.path !== '/dashboard/staff'
  );

  const currentNav = allNavItems.find(item => item.path !== '/dashboard' && location.pathname.startsWith(item.path));
  
  // Auth pages: hide GNB completely (Figma-style fullscreen)
  const isAuthPage = ['/login', '/signup', '/forgot-password'].includes(location.pathname);
  
  // GNB는 인증 페이지에서만 숨김. 나머지(알림/스탬프/쿠폰 상세/수정 포함)는 항상 노출.
  const hideGnb = isAuthPage;

  return (
    <div className={`modern-layout ${isAuthPage ? 'auth-page' : ''}`}>
      {/* 2-Tier Sticky GNB */}
      <header className={`gnb ${isScrolled ? 'scrolled' : ''} ${isMenuOpen ? 'menu-open' : ''}`}>
        {/* Top Tier: Logo and Global Actions */}
        <div className="gnb-top">
          <div className="gnb-container">
            {/* 모바일: ☰ 왼쪽 고정 */}
            <button className="gnb-icon-btn menu-toggle-btn mobile-only" onClick={() => setIsMenuOpen(!isMenuOpen)}>
              {isMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>

            <Link to="/dashboard" className="gnb-logo">PathWave</Link>
            
            <div className="gnb-actions">
              {/* PC+모바일 공통: 사람 아이콘 (회원정보/직원관리) + 설정 아이콘 */}
              <button
                className="gnb-icon-btn"
                onClick={() => { navigate('/dashboard/staff'); setIsMenuOpen(false); }}
                aria-label="회원정보/직원관리"
              >
                <User size={20} />
              </button>
              <button
                className="gnb-icon-btn"
                onClick={() => { navigate('/dashboard/settings'); setIsMenuOpen(false); }}
                aria-label="설정"
              >
                <Settings size={20} />
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Tier: 1-Depth Menus (모바일: 설정/직원관리 제외) */}
        <div className="gnb-bottom">
          <div className="gnb-bottom-container" style={{ position: 'relative' }}>
            {showLeftScroll && (
              <button className="nav-scroll-indicator left" onClick={() => scrollNav('left')} aria-label="왼쪽으로 스크롤">
                <ChevronLeft size={16} />
              </button>
            )}
            <nav className="gnb-nav-horizontal" ref={navRef} onScroll={handleNavScroll}>
              {gnbNavItems.map(item => (
                  <NavLink 
                    key={item.path} 
                    to={item.path}
                    end={item.end}
                    className={({isActive}) => `gnb-link ${isActive ? 'active' : ''}`}
                  >
                    {item.label}
                  </NavLink>
              ))}
            </nav>
            {showRightScroll && (
              <button className="nav-scroll-indicator right" onClick={() => scrollNav('right')} aria-label="오른쪽으로 스크롤">
                <ChevronRight size={16} />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay (전체 메뉴 — 설정 포함) */}
      {isMenuOpen && (
        <div className="mobile-overlay" onClick={() => setIsMenuOpen(false)}>
          <nav className="mobile-nav" onClick={e => e.stopPropagation()}>
            {allNavItems.map(item => (
              <NavLink 
                key={item.path} 
                to={item.path} 
                className="mobile-link"
                onClick={() => setIsMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      )}

      <main className="main-viewport">
        <div className="container">
          <Outlet />
        </div>
      </main>

      {/* 공통 푸터 — 인증 페이지 제외 */}
      {!isAuthPage && (
        <footer className="layout-footer">
          <div className="layout-footer-inner">
            <div className="layout-footer-links">
              <button className="layout-footer-link">고객센터</button>
              <span className="layout-footer-divider">|</span>
              <button className="layout-footer-link">자주묻는 질문</button>
              <span className="layout-footer-divider">|</span>
              <button className="layout-footer-link">서비스이용약관</button>
            </div>
            <p className="layout-footer-notice">
              ※ BE서비스는 서비스플랫폼으로 플랫폼내에서 제공되는 정보 및 이벤트, 혜택 등…은 등록 업체에 책임이 있습니다.
            </p>
            <div className="layout-footer-company">
              <p style={{ fontWeight: 600, marginBottom: '2px' }}>시원컴퍼니 Copyright 2023, siwon company. All rights reserved.</p>
              <p>서울특별시 서초구 메헌로 26(하이브랜드 1312,1313층) 02-1234-5678</p>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
};

export default DashboardLayout;
