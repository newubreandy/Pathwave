import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { adminLogin } from '../services/auth.js';
import './Login.css';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await adminLogin(email.trim().toLowerCase(), password);
      // PR #60 — 401 redirect 의 ?from=... 또는 RequireAuth 의 state.from 복귀
      const params = new URLSearchParams(location.search);
      const fromQuery = params.get('from');
      const from = location.state?.from?.pathname || fromQuery || '/dashboard';
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || '로그인에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        {/* pathwave 공통 로고 — 마크 SVG + 옆 소문자 텍스트. */}
        <div className="login-brand" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img src="/pathwave_lockup.svg" alt="pathwave" style={{ height: 40, display: 'block' }} />
          </div>
          <div className="login-sub">admin</div>
        </div>

        <label className="login-label">
          <span>이메일</span>
          <input
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@pathwave.kr"
            required
            autoFocus
          />
        </label>

        <label className="login-label">
          <span>비밀번호</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </label>

        {error && <div className="login-error">{error}</div>}

        <button
          type="submit"
          className="btn btn-primary login-submit"
          disabled={loading}
        >
          {loading ? '로그인 중...' : '로그인'}
        </button>

        <p className="login-hint">
          Super Admin 계정만 접근 가능합니다.
          <br />
          (사장/직원/일반 사용자 계정 거부)
        </p>
      </form>
    </div>
  );
}
