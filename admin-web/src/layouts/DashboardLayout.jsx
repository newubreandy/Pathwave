import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, Link, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Radio, UserCheck, Battery, Megaphone, CreditCard,
  FileText, LogOut, Search, Languages, Ticket, MessageSquare, Users,
  HelpCircle, BookOpen, BarChart2, ChevronDown, ChevronRight, Building2,
  Flag, Bell, Smartphone, KeyRound, Activity, DollarSign, PackageCheck,
  Palette,
  ToggleRight,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { adminLogout, getCurrentAdmin } from '../services/auth.js';
import { adminApi } from '../services/admin.js';
// PwFooter import 제거 (2026-05-27) — 슈퍼어드민에 푸터 불필요
import ChangePasswordModal from '../components/ChangePasswordModal.jsx';
import CriticalAdminAlert from '../components/CriticalAdminAlert.jsx';
import './DashboardLayout.css';

// ───────────────────────────────────────────────────────────────────────────
// LNB 그룹 — 5 섹션. 메뉴 수가 많아져 아코디언으로 묶음 (사용자 요구 2026-05-17).
// 각 그룹은 토글 가능. 현재 경로에 매칭되는 그룹은 자동으로 펼침.
// ───────────────────────────────────────────────────────────────────────────
const NAV_GROUPS = [
  {
    id: 'main',
    labelKey: 'nav.group_main',
    labelDefault: '메인',
    defaultOpen: true,
    items: [
      { to: '/dashboard',           icon: LayoutDashboard, labelKey: 'nav.dashboard',  end: true },
      { to: '/dashboard/beacons',   icon: Radio,           labelKey: 'nav.beacons'               },
      { to: '/dashboard/service-requests', icon: PackageCheck, labelKey: 'nav.service_requests', labelDefault: '서비스 신청 관리' },
      { to: '/dashboard/approvals', icon: UserCheck,       labelKey: 'nav.approvals',  badge: 3  },
    ],
  },
  {
    id: 'ops',
    labelKey: 'nav.group_ops',
    labelDefault: '운영',
    defaultOpen: true,
    items: [
      { to: '/dashboard/battery',       icon: Battery,        labelKey: 'nav.battery'        },
      { to: '/dashboard/announcements', icon: Megaphone,      labelKey: 'nav.announcements'  },
      { to: '/dashboard/notifications', icon: Bell,           labelKey: 'nav.notifications', labelDefault: '알림/부가서비스 관리' },
      { to: '/dashboard/users',         icon: Users,          labelKey: 'nav.users',         labelDefault: '사용자관리' },
      { to: '/dashboard/facilities',    icon: Building2,      labelKey: 'nav.facilities',    labelDefault: '매장관리' },
      // IA 감사 2026-06-09 — admin_extra_tools 비활성 시 자동 가림 (P2 이관)
      { to: '/dashboard/staff-monitor', icon: Users,          labelKey: 'nav.staff_monitor',  requiresFeature: 'admin_extra_tools' },
      { to: '/dashboard/chat-monitor',  icon: MessageSquare,  labelKey: 'nav.chat_monitor',   requiresFeature: 'admin_extra_tools' },
      { to: '/dashboard/abuse-reports', icon: Flag,           labelKey: 'nav.abuse_reports'  , labelDefault: '신고 처리' },
      { to: '/dashboard/banned-words',  icon: Flag,           labelKey: 'nav.banned_words',  labelDefault: '금지어 관리' },
    ],
  },
  {
    id: 'billing',
    labelKey: 'nav.group_billing',
    labelDefault: '결제·정책',
    defaultOpen: false,
    items: [
      { to: '/dashboard/payments',     icon: CreditCard, labelKey: 'nav.payments'     },
      { to: '/dashboard/policies',     icon: FileText,   labelKey: 'nav.policies'     },
      { to: '/dashboard/coupon-stats', icon: Ticket,     labelKey: 'nav.coupon_stats',   requiresFeature: 'admin_extra_tools' },
    ],
  },
  {
    id: 'support',
    labelKey: 'nav.group_support',
    labelDefault: '고객지원',
    defaultOpen: false,
    items: [
      { to: '/dashboard/support',       icon: HelpCircle,  labelKey: 'nav.support'       },
      { to: '/dashboard/faq',           icon: BookOpen,    labelKey: 'nav.faq'           },
      { to: '/dashboard/support/stats', icon: BarChart2,   labelKey: 'nav.support_stats', requiresFeature: 'admin_extra_tools' },
    ],
  },
  {
    id: 'system',
    labelKey: 'nav.group_system',
    labelDefault: '시스템',
    defaultOpen: false,
    items: [
      { to: '/dashboard/company-info', icon: Building2, labelKey: 'nav.company_info', labelDefault: '법인 정보' },
      { to: '/dashboard/categories',   icon: BookOpen,  labelKey: 'nav.categories',   labelDefault: '업종 카테고리' },
      { to: '/dashboard/app-versions', icon: Smartphone, labelKey: 'nav.app_versions', labelDefault: '앱 버전' },
      { to: '/dashboard/system-health', icon: Activity, labelKey: 'nav.system_health', labelDefault: '시스템 점검' },
      { to: '/dashboard/cost-monitor',  icon: DollarSign, labelKey: 'nav.cost_monitor',  labelDefault: 'AI 비용 모니터', requiresFeature: 'admin_extra_tools' },
      { to: '/dashboard/themes',       icon: Palette,   labelKey: 'nav.themes',       labelDefault: '앱 배경 테마' },
      { to: '/dashboard/features',     icon: ToggleRight, labelKey: 'nav.features',   labelDefault: 'Feature Flag' },
      { to: '/dashboard/i18n',         icon: Languages, labelKey: 'nav.i18n' },
    ],
  },
];

function groupForPath(pathname) {
  for (const g of NAV_GROUPS) {
    if (g.items.some((it) => it.to === pathname || pathname.startsWith(it.to + '/'))) {
      return g.id;
    }
  }
  return null;
}

export default function DashboardLayout() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const admin = getCurrentAdmin();
  const initial = (admin?.name?.[0] || admin?.email?.[0] || 'A').toUpperCase();

  // IA 감사 2026-06-09 — Feature Flag 조회. requiresFeature 마킹 메뉴 가림.
  const [features, setFeatures] = useState({});
  useEffect(() => {
    adminApi.listFeatures()
      .then((res) => {
        const map = {};
        for (const it of (res.items || [])) {
          map[it.key] = !!it.current_enabled;
        }
        setFeatures(map);
      })
      .catch(() => {});
  }, []);

  // 그룹 펼침 상태 — 현재 경로가 속한 그룹은 자동으로 열림
  const activeGroup = groupForPath(location.pathname);
  const [openGroups, setOpenGroups] = useState(() => {
    const init = {};
    NAV_GROUPS.forEach((g) => { init[g.id] = g.defaultOpen || g.id === activeGroup; });
    return init;
  });

  const [pwModalOpen, setPwModalOpen] = useState(false);

  function toggleGroup(id) {
    setOpenGroups((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function handleLogout() {
    adminLogout();
    navigate('/login', { replace: true });
  }

  function renderNavLink({ to, icon: Icon, labelKey, labelDefault, end, badge }) {
    return (
      <NavLink
        key={to} to={to} end={end}
        className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
      >
        <Icon size={17} strokeWidth={2} />
        <span>{t(labelKey, labelDefault)}</span>
        {badge != null && badge > 0 && <span className="nav-badge">{badge}</span>}
      </NavLink>
    );
  }

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        {/* 2026-05-27: 브랜드 클릭 시 메인 대시보드로 이동 */}
        {/* pathwave 공통 로고 — 가로 lockup (마크+wordmark 결합) */}
        <Link to="/dashboard" className="sidebar-brand" aria-label="pathwave 대시보드로 이동">
          <img src="/pathwave_lockup.svg" alt="pathwave" style={{ height: 28, display: 'block' }} />
          <div className="brand-text" style={{ display: 'none' }}>
            <div className="brand-title">pathwave</div>
            <div className="brand-sub">super admin</div>
          </div>
        </Link>

        <div className="sidebar-search">
          <Search size={14} />
          <input placeholder="Search..." />
          <span className="kbd"><span>⌘</span><span>K</span></span>
        </div>

        {NAV_GROUPS.map((g) => {
          const isOpen = openGroups[g.id];
          const isActive = activeGroup === g.id;
          return (
            <div key={g.id} className={'sidebar-group' + (isActive ? ' active' : '')}>
              <button
                type="button"
                className="sidebar-section sidebar-section--toggle"
                onClick={() => toggleGroup(g.id)}
                aria-expanded={isOpen}
              >
                <span>{t(g.labelKey, g.labelDefault)}</span>
                {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>
              {isOpen && (
                <nav className="sidebar-nav">
                  {/* IA 감사 2026-06-09 — requiresFeature 마킹된 항목은 Feature Flag 가 OFF 면 가림. */}
                  {g.items
                    .filter((it) => !it.requiresFeature || features[it.requiresFeature])
                    .map(renderNavLink)}
                </nav>
              )}
            </div>
          );
        })}

        <div className="sidebar-footer">
          {admin && (
            <div className="account">
              <div className="account-avatar">{initial}</div>
              <div className="account-meta">
                <div className="account-name">{admin.name || admin.email}</div>
                <div className="account-role">{admin.role || 'Super Admin'}</div>
              </div>
            </div>
          )}
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="logout-btn" type="button"
                    onClick={() => setPwModalOpen(true)}
                    style={{ flex: 1, minWidth: 0 }}>
              <KeyRound size={14} aria-hidden="true" />
              <span>비밀번호</span>
            </button>
            <button className="logout-btn" onClick={handleLogout}
                    style={{ flex: 1, minWidth: 0 }}>
              <LogOut size={14} aria-hidden="true" />
              <span>{t('nav.logout')}</span>
            </button>
          </div>
        </div>
      </aside>
      <ChangePasswordModal
        open={pwModalOpen}
        onClose={() => setPwModalOpen(false)}
      />
      <CriticalAdminAlert />

      <main className="admin-main">
        <Outlet />
        {/* 2026-05-27: 푸터 제거 — 슈퍼어드민(운영자 내부 도구)은 법적 표기 의무 X.
            업계 표준 (AWS Console / Stripe Dashboard / Vercel 등) 동일 — admin UI 는 푸터 없음. */}
      </main>
    </div>
  );
}
