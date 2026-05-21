import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthService from '../services/auth/AuthService';
import './Login.css';

/**
 * 시설 사장님 비밀번호 재설정 — 2단계.
 *   1) 이메일 입력 → 인증 코드 발송 (POST /api/facility/forgot-password)
 *   2) 코드 + 새 비밀번호 → 재설정 (POST /api/facility/reset-password)
 */
const ForgotPassword = () => {
  const navigate = useNavigate();
  const [step, setStep]       = useState(1);   // 1=이메일 / 2=코드+새 비번
  const [email, setEmail]     = useState('');
  const [code, setCode]       = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [info, setInfo]       = useState('');

  const requestCode = async (e) => {
    e.preventDefault();
    setError(''); setInfo('');
    setLoading(true);
    try {
      const res = await AuthService.forgotPassword(email.trim());
      setInfo(res?.message || '인증 코드를 발송했습니다. 이메일을 확인해 주세요.');
      setStep(2);
    } catch (err) {
      setError(err?.message || '코드 발송에 실패했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setLoading(false);
    }
  };

  const submitReset = async (e) => {
    e.preventDefault();
    setError(''); setInfo('');
    if (password !== confirm) {
      setError('새 비밀번호가 일치하지 않습니다.');
      return;
    }
    if (password.length < 8) {
      setError('비밀번호는 8자 이상이어야 합니다.');
      return;
    }
    setLoading(true);
    try {
      await AuthService.resetPassword(email.trim(), code.trim(), password);
      setInfo('비밀번호가 재설정되었습니다. 로그인 화면으로 이동합니다.');
      setTimeout(() => navigate('/login', { replace: true }), 1200);
    } catch (err) {
      setError(err?.message || '재설정에 실패했습니다. 코드를 다시 확인해 주세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modern-auth-page">
      <div className="auth-logo">
        <span className="auth-logo-text">PathWave</span>
        <span className="auth-logo-sub">SERVICE PROVIDER</span>
      </div>

      <div className="auth-container">
        {step === 1 ? (
          <form className="modern-form" onSubmit={requestCode}>
            <div className="input-group-modern">
              <label htmlFor="fp-email">EMAIL</label>
              <input
                id="fp-email" type="email" required className="input-modern"
                placeholder="name@example.com" value={email}
                onChange={(e) => setEmail(e.target.value)} autoComplete="email"
              />
            </div>
            {error && <p style={MSG.err}>{error}</p>}
            <div className="auth-actions">
              <button type="submit" className="btn-modern btn-modern-primary full-width"
                      disabled={loading}>
                {loading ? '발송 중...' : '인증 코드 받기'}
              </button>
              <div className="auth-links">
                <Link to="/login" className="link-text">로그인으로 돌아가기</Link>
              </div>
            </div>
          </form>
        ) : (
          <form className="modern-form" onSubmit={submitReset}>
            {info && <p style={MSG.info}>{info}</p>}
            <div className="input-group-modern">
              <label htmlFor="fp-code">인증 코드</label>
              <input
                id="fp-code" type="text" inputMode="numeric" required
                className="input-modern" placeholder="이메일로 받은 6자리 코드"
                value={code} onChange={(e) => setCode(e.target.value)}
              />
            </div>
            <div className="input-group-modern">
              <label htmlFor="fp-pw">새 비밀번호</label>
              <input
                id="fp-pw" type="password" required className="input-modern"
                placeholder="영문·숫자·특수문자 8자 이상" value={password}
                onChange={(e) => setPassword(e.target.value)} autoComplete="new-password"
              />
            </div>
            <div className="input-group-modern">
              <label htmlFor="fp-pw2">새 비밀번호 확인</label>
              <input
                id="fp-pw2" type="password" required className="input-modern"
                placeholder="새 비밀번호 다시 입력" value={confirm}
                onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password"
              />
            </div>
            {error && <p style={MSG.err}>{error}</p>}
            <div className="auth-actions">
              <button type="submit" className="btn-modern btn-modern-primary full-width"
                      disabled={loading}>
                {loading ? '재설정 중...' : '비밀번호 재설정'}
              </button>
              <div className="auth-links">
                <button
                  type="button" className="link-text"
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                  onClick={() => { setStep(1); setError(''); setInfo(''); }}
                >
                  이메일 다시 입력
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

const MSG = {
  err:  { color: 'var(--pw-error, #EF4444)',   fontSize: 13, margin: '4px 0 0' },
  info: { color: 'var(--pw-primary, #22C55E)', fontSize: 13, margin: '0 0 12px' },
};

export default ForgotPassword;
