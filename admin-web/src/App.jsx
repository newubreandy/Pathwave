import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout.jsx';
import RequireAuth from './layouts/RequireAuth.jsx';
import DevPreviewBar from './components/DevPreviewBar.jsx';
import Login from './pages/Login.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Beacons from './pages/Beacons.jsx';
import Approvals from './pages/Approvals.jsx';
import Battery from './pages/Battery.jsx';
import Announcements from './pages/Announcements.jsx';
import Payments from './pages/Payments.jsx';
import Policies from './pages/Policies.jsx';
import Translations from './pages/Translations.jsx';
import CouponStats from './pages/CouponStats.jsx';
import ChatMonitor from './pages/ChatMonitor.jsx';
import StaffMonitor from './pages/StaffMonitor.jsx';
import Support from './pages/Support.jsx';
import Faq from './pages/Faq.jsx';
import SupportStats from './pages/SupportStats.jsx';
import CompanyInfo from './pages/CompanyInfo.jsx';

const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
};

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <DevPreviewBar />
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<RequireAuth><DashboardLayout /></RequireAuth>}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/beacons" element={<Beacons />} />
          <Route path="/dashboard/approvals" element={<Approvals />} />
          <Route path="/dashboard/battery" element={<Battery />} />
          <Route path="/dashboard/announcements" element={<Announcements />} />
          <Route path="/dashboard/payments" element={<Payments />} />
          <Route path="/dashboard/policies" element={<Policies />} />
          <Route path="/dashboard/coupon-stats" element={<CouponStats />} />
          <Route path="/dashboard/chat-monitor" element={<ChatMonitor />} />
          <Route path="/dashboard/staff-monitor" element={<StaffMonitor />} />
          <Route path="/dashboard/i18n" element={<Translations />} />
          <Route path="/dashboard/support" element={<Support />} />
          <Route path="/dashboard/faq" element={<Faq />} />
          <Route path="/dashboard/support/stats" element={<SupportStats />} />
          <Route path="/dashboard/company-info" element={<CompanyInfo />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
