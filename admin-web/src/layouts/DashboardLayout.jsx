import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Radio, UserCheck, Battery, Megaphone, CreditCard,
  FileText, LogOut, Search, Languages, Ticket, MessageSquare, Users,
  HelpCircle, BookOpen, BarChart2, ChevronDown, ChevronRight, Building2,
  Flag, Bell, Smartphone, KeyRound, Activity, DollarSign,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { adminLogout, getCurrentAdmin } from '../services/auth.js';
import PwFooter from '../components/common/PwFooter.jsx';
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
      { to: '/dashboard/notifications', icon: Bell,           labelKey: 'nav.notifications', labelDefault: '알림 검토' },
      { to: '/dashboard/users',         icon: Users,          labelKey: 'nav.users',         labelDefault: '회원 관리' },
      { to: '/dashboard/staff-monitor', icon: Users,          labelKey: 'nav.staff_monitor'  },
      { to: '/dashboard/chat-monitor',  icon: MessageSquare,  labelKey: 'nav.chat_monitor'   },
      { to: '/dashboard/abuse-reports', icon: Flag,           labelKey: 'nav.abuse_reports'  },
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
      { to: '/dashboard/coupon-stats', icon: Ticket,     labelKey: 'nav.coupon_stats' },
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
      { to: '/dashboard/support/stats', icon: BarChart2,   labelKey: 'nav.support_stats' },
    ],
  },
  {
    id: 'system',
    labelKey: 'nav.group_system',
    labelDefault: '시스템',
    defaultOpen: false,
    items: [
      { to: '/dashboard/company-info', icon: Building2, labelKey: 'nav.company_info', labelDefault: '법인 정보' },
      { to: '/dashboard/app-versions', icon: Smartphone, labelKey: 'nav.app_versions', labelDefault: '앱 버전' },
      { to: '/dashboard/system-health', icon: Activity, labelKey: 'nav.system_health', labelDefault: '시스템 점검' },
      { to: '/dashboard/cost-monitor',  icon: DollarSign, labelKey: 'nav.cost_monitor',  labelDefault: 'AI 비용 모니터' },
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

  function renderNavLink({ to, icon: Icon, labelKey, end, badge }) {
    return (
      <NavLink
        key={to} to={to} end={end}
        className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
      >
        <Icon size={17} strokeWidth={2} />
        <span>{t(labelKey)}</span>
        {badge != null && badge > 0 && <span className="nav-badge">{badge}</span>}
      </NavLink>
    );
  }

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">PW</div>
          <div className="brand-text">
            <div className="brand-title">PathWave</div>
            <div className="brand-sub">Super Admin</div>
          </div>
        </div>

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
                  {g.items.map(renderNavLink)}
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
          <div style={{ display: 'flex', gap: 4 }}>
            <button className="logout-btn" type="button"
                    onClick={() => setPwModalOpen(true)}
                    aria-label="비밀번호 변경"
                    style={{ flex: '0 0 auto', padding: '8px 10px' }}>
              <KeyRound size={14} aria-hidden="true" />
            </button>
            <button className="logout-btn" onClick={handleLogout}
                    style={{ flex: 1 }}>
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
        <PwFooter />
      </main>
    </div>
  );
}
