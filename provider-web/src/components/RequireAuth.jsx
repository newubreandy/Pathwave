import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import AuthService from '../services/auth/AuthService';

/**
 * 인증 가드 — 토큰이 없으면 /login 으로 리다이렉트.
 * 이전 경로는 state.from 으로 넘겨 로그인 후 복귀 가능.
 *
 * P4 fix (2026-05-27): DEV_AUTO_LOGIN 자동 mock 세션 제거.
 * dev 환경 진입은 scripts/seed_dev_provider.py 로 발급한 계정으로 진짜 로그인.
 * 이 mock 세션은 백엔드와 토큰이 일치하지 않아 모든 API 401 →
 * /login redirect 무한 사이클 + 화면이 빈 상태로 보임. 차단.
 */
const RequireAuth = ({ children }) => {
  const location = useLocation();
  if (!AuthService.isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
};

export default RequireAuth;
