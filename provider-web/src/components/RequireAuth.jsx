import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import AuthService from '../services/auth/AuthService';

/**
 * 인증 가드 — 토큰이 없으면 /login 으로 리다이렉트.
 * 이전 경로는 state.from 으로 넘겨 로그인 후 복귀 가능.
 *
 * DEV_AUTO_LOGIN — 개발(`vite dev`) 환경에서만 토큰 없이 대시보드 진입을
 *   허용하는 편의 기능. 출시 빌드(`vite build`)에서는 `import.meta.env.DEV`
 *   가 false 이므로 자동으로 비활성화되어 실 인증이 강제된다.
 */
const DEV_AUTO_LOGIN = import.meta.env.DEV;

const seedMockSession = () => {
  localStorage.setItem('pathwave_token', 'dev-auto-token');
  localStorage.setItem('pathwave_user', JSON.stringify({
    id:    'siwon-001',
    email: 'admin@pathwave.com',
    name:  '시원컴퍼니',
    role:  'OWNER',
  }));
};

const RequireAuth = ({ children }) => {
  const location = useLocation();
  if (!AuthService.isAuthenticated()) {
    if (DEV_AUTO_LOGIN) {
      seedMockSession();
      return children;
    }
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
};

export default RequireAuth;
