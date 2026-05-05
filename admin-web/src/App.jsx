import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout.jsx';
import RequireAuth from './layouts/RequireAuth.jsx';
import Login from './pages/Login.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Beacons from './pages/Beacons.jsx';
import Approvals from './pages/Approvals.jsx';
import Battery from './pages/Battery.jsx';
import Announcements from './pages/Announcements.jsx';
import Payments from './pages/Payments.jsx';
import Policies from './pages/Policies.jsx';

const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
};

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
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
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
