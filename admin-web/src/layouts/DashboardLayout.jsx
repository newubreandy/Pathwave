import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Radio, UserCheck, Battery, Megaphone, CreditCard,
  FileText, LogOut, Search, Languages,
} from 'lucide-react';
import { adminLogout, getCurrentAdmin } from '../services/auth.js';
import './DashboardLayout.css';

const NAV_PRIMARY = [
  { to: '/dashboard',                icon: LayoutDashboard, label: '대시보드',     end: true },
  { to: '/dashboard/beacons',        icon: Radio,           label: '비콘 인벤토리'  },
  { to: '/dashboard/approvals',      icon: UserCheck,       label: '사장 가입 승인', badge: 3 },
];

const NAV_OPS = [
  { to: '/dashboard/battery',        icon: Battery,         label: '배터리 모니터링' },
  { to: '/dashboard/announcements',  icon: Megaphone,       label: '시스템 공지'    },
  { to: '/dashboard/payments',       icon: CreditCard,      label: '결제 / 구독'    },
  { to: '/dashboard/policies',       icon: FileText,        label: '약관 / 정책'    },
  { to: '/dashboard/i18n',           icon: Languages,       label: 'i18n 관리'      },
];

export default function DashboardLayout() {
  const navigate = useNavigate();
  const admin = getCurrentAdmin();
  const initial = (admin?.name?.[0] || admin?.email?.[0] || 'A').toUpperCase();

  function handleLogout() {
    adminLogout();
    navigate('/login', { replace: true });
  }

  function renderNavLink({ to, icon: Icon, label, end, badge }) {
    return (
      <NavLink
        key={to} to={to} end={end}
        className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
      >
        <Icon size={17} strokeWidth={2} />
        <span>{label}</span>
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

        <div className="sidebar-section">메인</div>
        <nav className="sidebar-nav">{NAV_PRIMARY.map(renderNavLink)}</nav>

        <div className="sidebar-section">운영</div>
        <nav className="sidebar-nav">{NAV_OPS.map(renderNavLink)}</nav>

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
          <button className="logout-btn" onClick={handleLogout}>
            <LogOut size={14} />
            <span>로그아웃</span>
          </button>
        </div>
      </aside>

      <main className="admin-main">
        <Outlet />
      </main>
    </div>
  );
}
