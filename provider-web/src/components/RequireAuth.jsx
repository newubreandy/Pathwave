import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import AuthService from '../services/auth/AuthService';

/**
 * 인증 가드 — 토큰이 없으면 /login 으로 리다이렉트.
 * 이전 경로는 state.from 으로 넘겨 로그인 후 복귀 가능.
 */
const RequireAuth = ({ children }) => {
  const location = useLocation();
  if (!AuthService.isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
};

export default RequireAuth;
