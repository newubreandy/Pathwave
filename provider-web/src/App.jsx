import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import RequireAuth from './components/RequireAuth';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import StoreInfo from './pages/StoreInfo';
import WifiSettings from './pages/WifiSettings';
import Facilities from './pages/Facilities';
import CustomerChat from './pages/CustomerChat';
import Notifications from './pages/Notifications';
import Stamps from './pages/Stamps';
import StampForm from './pages/StampForm';
import Coupons from './pages/Coupons';
import CouponForm from './pages/CouponForm';
import Settings from './pages/Settings';
import MemberProfile from './pages/MemberProfile';
import StaffManagement from './pages/StaffManagement';
import PaymentManagement from './pages/PaymentManagement';
import ServiceRequest from './pages/ServiceRequest';

// 페이지 전환 시 스크롤 상단으로 리셋
const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

const ReportManagement = () => <div className="modern-page"><div className="page-header-section"><h1 className="page-title">리포트</h1><p className="sub-title">매장 방문객 및 매출, 스탬프 사용 통계를 확인합니다.</p></div><div className="card" style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-hint)' }}>차트 데이터가 준비 중입니다.</div></div>;

function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Routes>
        {/* 공개 — 인증 불필요 */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* 보호 — 토큰 없으면 /login 으로 강제 리다이렉트 */}
        <Route element={<RequireAuth><DashboardLayout /></RequireAuth>}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/store" element={<StoreInfo />} />
          <Route path="/dashboard/report" element={<ReportManagement />} />
          <Route path="/dashboard/wifi" element={<WifiSettings />} />
          <Route path="/dashboard/service-request" element={<ServiceRequest />} />
          <Route path="/dashboard/staff" element={<StaffManagement />} />
          <Route path="/dashboard/notifications" element={<Notifications />} />
          <Route path="/dashboard/stamps" element={<Stamps />} />
          <Route path="/dashboard/stamps/:action/:id?" element={<StampForm />} />
          <Route path="/dashboard/coupons" element={<Coupons />} />
          <Route path="/dashboard/coupons/:action/:id?" element={<CouponForm />} />
          <Route path="/dashboard/payments" element={<PaymentManagement />} />
          <Route path="/dashboard/settings" element={<Settings />} />
          <Route path="/dashboard/profile" element={<Navigate to="/dashboard/staff" replace />} />
          <Route path="/dashboard/chat" element={<CustomerChat />} />
        </Route>

        {/* Fallback — 알 수 없는 경로는 인증 상태에 따라 분기 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
