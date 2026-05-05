import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { adminLogin } from '../services/auth.js';
import './Login.css';

export default function Login() {
  const navigate = useNavigate();
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
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.message || '로그인에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-brand">
          <ShieldCheck size={32} strokeWidth={1.75} />
          <div>
            <div className="login-title">PathWave Admin</div>
            <div className="login-sub">운영자 콘솔</div>
          </div>
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
