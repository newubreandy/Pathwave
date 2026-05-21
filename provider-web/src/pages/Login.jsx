import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import AuthService from '../services/auth/AuthService';
import { useDialog } from '../components/common/DialogProvider';
import './Login.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { alert } = useDialog();

  // 이미 로그인된 사용자는 대시보드로 즉시 이동.
  // ⚠ TEMP (사용자 요구 2026-05-11): 백엔드 인증 연동 전, /login 진입 시
  //    토큰이 없으면 mock 세션을 자동 발급하고 곧바로 대시보드로 이동.
  //    실 인증 연동 시 아래 자동 mock 발급 라인 제거.
  useEffect(() => {
    if (!AuthService.isAuthenticated()) {
      localStorage.setItem('pathwave_token', 'dev-auto-token');
      localStorage.setItem('pathwave_user', JSON.stringify({
        id: 'siwon-001',
        email: 'admin@pathwave.com',
        name: '시원컴퍼니',
        role: 'OWNER',
      }));
    }
    navigate('/dashboard', { replace: true });
  }, [navigate]);

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
      alert('Login failed. Please check your credentials.');
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
    </div>
  );
};

export default Login;
