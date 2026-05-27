import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import AuthService from '../services/auth/AuthService';
import { useConfirm } from '../hooks/useConfirm';
import './Login.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { alert: alertModal, modal: confirmModal } = useConfirm();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // P4 fix (2026-05-27): 이미 로그인된 사용자만 dashboard 로 redirect.
  // 자동 mock 세션 발급 제거 — 401 후 /login?from=... 진입 시 무한 루프 차단.
  // 진짜 로그인은 form 으로만 가능 (P4 인증 우회 차단).
  useEffect(() => {
    if (AuthService.isAuthenticated()) {
      // 이미 토큰 있음 → from 쿼리 / state 또는 dashboard
      const params = new URLSearchParams(location.search);
      const fromQuery = params.get('from');
      const from = location.state?.from?.pathname || fromQuery || '/dashboard';
      navigate(from, { replace: true });
    }
    // 토큰 없으면 로그인 화면 머무름.
  }, [navigate, location]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await AuthService.login(email, password);
      // PR #60 — RequireAuth (state.from) 또는 401 redirect (?from=...) 모두 지원
      const params = new URLSearchParams(location.search);
      const fromQuery = params.get('from');
      const from = location.state?.from?.pathname || fromQuery || '/dashboard';
      navigate(from, { replace: true });
    } catch (error) {
      await alertModal({ title: '로그인 실패', desc: '이메일과 비밀번호를 확인해 주세요.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modern-auth-page">
      {/* Logo — Figma style centered branding */}
      <div className="auth-logo">
        <span className="auth-logo-text">PathWave</span>
        <span className="auth-logo-sub">SERVICE PROVIDER</span>
      </div>

      <div className="auth-container">
        <form className="modern-form" onSubmit={handleLogin}>
          <div className="input-group-modern">
            <label htmlFor="login-email">EMAIL</label>
            <input 
              id="login-email"
              type="email" 
              placeholder="name@example.com" 
              required 
              className="input-modern" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </div>
          
          <div className="input-group-modern">
            <label htmlFor="login-password">PASSWORD</label>
            <input 
              id="login-password"
              type="password" 
              placeholder="••••••••" 
              required 
              className="input-modern" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <div className="auth-actions">
            <button type="submit" className="btn-modern btn-modern-primary full-width" disabled={loading}>
              {loading ? 'SIGNING IN...' : 'SIGN IN'}
            </button>
            <div className="auth-links">
              <Link to="/signup" className="link-text">CREATE ACCOUNT</Link>
              <span className="divider">/</span>
              <Link to="/forgot-password" className="link-text">FORGOT PASSWORD</Link>
            </div>
          </div>
        </form>
      </div>
      {confirmModal}
    </div>
  );
};

export default Login;
