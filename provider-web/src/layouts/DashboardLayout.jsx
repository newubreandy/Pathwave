import React, { useState, useEffect, useRef } from 'react';
import { Outlet, NavLink, Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Menu, X, ChevronLeft, ChevronRight, User, Settings, Bell, HelpCircle } from 'lucide-react';
import { getUnreadCount } from '../services/notification/mockInbox';
import PwFooter from '../components/common/PwFooter';
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

  // IA 감사 2026-06-09 — 13항목 1차원 → 4 그룹화 + 중복 해소
  // (P1 채팅 마케팅 그룹으로 이동, P2 staff GNB 중복 제거는 아래 GNB 영역 처리,
  //  P3 설정은 GNB 만 유지하기 위해 메인 메뉴에서 제거, P4 알림 라벨 명확화.)
  const navGroups = [
    {
      key: 'store',
      label: t('menu.group.store', '매장 운영'),
      items: [
        { path: '/dashboard/store',        label: t('menu.store',         '매장 관리') },   // P6 라벨 변경
        { path: '/dashboard/menu',         label: t('menu.menuManagement','메뉴 관리') },
        { path: '/dashboard/wifi',         label: t('menu.wifi',          '와이파이') },
      ],
    },
    {
      key: 'marketing',
      label: t('menu.group.marketing', '마케팅'),
      items: [
        { path: '/dashboard/chat',          label: t('menu.chat',          '채팅') },
        { path: '/dashboard/stamps',        label: t('menu.stamps',        '스탬프') },
        { path: '/dashboard/coupons',       label: t('menu.coupons',       '쿠폰') },
        { path: '/dashboard/notifications', label: t('menu.notifications', '알림 발송') },
      ],
    },
    {
      key: 'ops',
      label: t('menu.group.ops', '운영'),
      items: [
        { path: '/dashboard/report',          label: t('menu.report',         '리포트') },
        { path: '/dashboard/payments',        label: t('menu.payments',       '결제 관리') },
        { path: '/dashboard/service-request', label: t('menu.serviceRequest', '서비스 신청') },
        { path: '/dashboard/staff',           label: t('menu.staff',          '직원 관리') },
      ],
    },
    {
      key: 'support',
      label: t('menu.group.support', '지원'),
      items: [
        { path: '/dashboard/support', label: t('menu.support', '고객센터') },
      ],
    },
  ];

  // 평탄화 — 현재 페이지 매칭 등 호환용.
  const allNavItems = navGroups.flatMap(g => g.items);

  // GNB 수평 메뉴 항목 — 메인 메뉴에서 설정 이미 제거됨. 변경 X.
  const gnbNavItems = allNavItems;

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

            <Link to="/dashboard" className="gnb-logo" aria-label="pathwave"
                  style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <img src="/pathwave_lockup.svg" alt="pathwave" style={{ height: 26, display: 'block' }} />
            </Link>
            
            <div className="gnb-actions">
              {/* Notification Center 진입점 (사용자 요구 2026-05-10) — Bell + unread badge */}
              <button
                className="gnb-icon-btn gnb-bell"
                onClick={() => { navigate('/dashboard/notifications?tab=inbox'); setIsMenuOpen(false); }}
                aria-label="알림 (받은 알림)"
              >
                <Bell size={20} />
                {getUnreadCount() > 0 && (
                  <span className="gnb-bell-badge" aria-label={`읽지 않은 알림 ${getUnreadCount()}개`}>
                    {getUnreadCount() > 99 ? '99+' : getUnreadCount()}
                  </span>
                )}
              </button>
              {/* IA 감사 2026-06-09 — P2 중복 해소: GNB 의 직원 관리 아이콘 제거.
                  직원 관리는 메인 LNB "운영" 그룹에서 진입한다.
                  설정은 GNB 만 유지 (글로벌 도구) — 메인 메뉴에서 제거됨. */}
              <button
                className="gnb-icon-btn"
                onClick={(e) => { navigate('/dashboard/settings'); setIsMenuOpen(false); e.currentTarget.blur(); }}
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

      {/* 공통 푸터 — 인증 페이지 제외. 3 콘솔 공통 PwFooter 사용. */}
      {!isAuthPage && <PwFooter />}
    </div>
  );
};

export default DashboardLayout;
