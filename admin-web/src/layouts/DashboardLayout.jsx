import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Radio, UserCheck, Battery, Megaphone, LogOut,
} from 'lucide-react';
import { adminLogout, getCurrentAdmin } from '../services/auth.js';
import './DashboardLayout.css';

const NAV_ITEMS = [
  { to: '/dashboard',                icon: LayoutDashboard, label: '대시보드',     end: true },
  { to: '/dashboard/beacons',        icon: Radio,           label: '비콘 인벤토리'  },
  { to: '/dashboard/approvals',      icon: UserCheck,       label: '사장 가입 승인' },
  { to: '/dashboard/battery',        icon: Battery,         label: '배터리 모니터링'},
  { to: '/dashboard/announcements',  icon: Megaphone,       label: '시스템 공지'    },
];

export default function DashboardLayout() {
  const navigate = useNavigate();
  const admin = getCurrentAdmin();

  function handleLogout() {
    adminLogout();
    navigate('/login', { replace: true });
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

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                'nav-link' + (isActive ? ' active' : '')
              }
            >
              <Icon size={18} strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          {admin && (
            <div className="account">
              <div className="account-name">{admin.name || admin.email}</div>
              <div className="account-role">{admin.role}</div>
            </div>
          )}
          <button className="btn btn-ghost logout-btn" onClick={handleLogout}>
            <LogOut size={16} />
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
