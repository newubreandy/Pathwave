import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Radio, UserCheck, Battery, Megaphone, CreditCard,
  FileText, LogOut, Search, Languages, Ticket, MessageSquare,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { adminLogout, getCurrentAdmin } from '../services/auth.js';
import './DashboardLayout.css';

const NAV_PRIMARY_DEFS = [
  { to: '/dashboard',                icon: LayoutDashboard, labelKey: 'nav.dashboard',  end: true },
  { to: '/dashboard/beacons',        icon: Radio,           labelKey: 'nav.beacons'               },
  { to: '/dashboard/approvals',      icon: UserCheck,       labelKey: 'nav.approvals',  badge: 3  },
];

const NAV_OPS_DEFS = [
  { to: '/dashboard/battery',        icon: Battery,         labelKey: 'nav.battery'        },
  { to: '/dashboard/announcements',  icon: Megaphone,       labelKey: 'nav.announcements'  },
  { to: '/dashboard/payments',       icon: CreditCard,      labelKey: 'nav.payments'       },
  { to: '/dashboard/policies',       icon: FileText,        labelKey: 'nav.policies'       },
  { to: '/dashboard/coupon-stats',   icon: Ticket,          labelKey: 'nav.coupon_stats'   },
  { to: '/dashboard/chat-monitor',   icon: MessageSquare,   labelKey: 'nav.chat_monitor'   },
  { to: '/dashboard/i18n',           icon: Languages,       labelKey: 'nav.i18n'           },
];

export default function DashboardLayout() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const admin = getCurrentAdmin();
  const initial = (admin?.name?.[0] || admin?.email?.[0] || 'A').toUpperCase();

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

        <div className="sidebar-section">메인</div>
        <nav className="sidebar-nav">{NAV_PRIMARY_DEFS.map(renderNavLink)}</nav>

        <div className="sidebar-section">운영</div>
        <nav className="sidebar-nav">{NAV_OPS_DEFS.map(renderNavLink)}</nav>

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
            <span>{t('nav.logout')}</span>
          </button>
        </div>
      </aside>

      <main className="admin-main">
        <Outlet />
      </main>
    </div>
  );
}
