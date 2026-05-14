import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import AuthService from '../services/auth/AuthService';

/**
 * 인증 가드 — 토큰이 없으면 /login 으로 리다이렉트.
 * 이전 경로는 state.from 으로 넘겨 로그인 후 복귀 가능.
 *
 * ⚠ TEMP (사용자 요구 2026-05-11): 백엔드 인증 연동 전,
 *    토큰 없으면 mock 세션을 자동 발급해 대시보드에 바로 진입하도록 처리.
 *    실 인증 연동 시 아래 DEV_AUTO_LOGIN 블록 제거하고 isAuthenticated 검사
 *    실패 시 /login 리다이렉트로 복원할 것.
 */
const DEV_AUTO_LOGIN = true;

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
