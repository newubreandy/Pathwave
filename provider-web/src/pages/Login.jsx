import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthService from '../services/auth/AuthService';
import './Login.css';

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await AuthService.login(email, password);
      navigate('/dashboard');
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

          {/* TODO: 인증 구축 후 제거 */}
          <button
            type="button"
            className="btn-modern btn-modern-outline full-width"
            style={{ marginTop: 'var(--pw-space-10)', opacity: 0.5, fontSize: 'var(--pw-caption-size)' }}
            onClick={() => navigate('/dashboard')}
          >
            DEV MODE — 바로 들어가기
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
