import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthService from '../services/auth/AuthService';
import { useConfirm } from '../hooks/useConfirm';
import './Login.css';

/**
 * ForgotPassword — 시설(점주) 비밀번호 재설정.
 *
 * 2단계: ① 이메일 입력 → 인증 코드 발송 → ② 코드 + 새 비밀번호 → 재설정 → 로그인.
 * 백엔드: POST /api/facility/forgot-password, POST /api/facility/reset-password.
 * 계정 열거 방지를 위해 forgot 응답은 가입 여부와 무관하게 항상 성공.
 */
const ForgotPassword = () => {
  const navigate = useNavigate();
  const { alert: alertModal, modal: confirmModal } = useConfirm();
  const [step, setStep] = useState('email');     // 'email' | 'reset'
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendCode = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await AuthService.forgotPassword(email);
      await alertModal({
        title: '인증 코드 발송',
        desc: '가입된 이메일이라면 인증 코드를 발송했습니다. 메일함을 확인해 주세요. (5분 유효)',
      });
      setStep('reset');
    } catch {
      await alertModal({ title: '오류', desc: '잠시 후 다시 시도해 주세요.' });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async (e) => {
    e.preventDefault();
    if (password !== password2) {
      await alertModal({ title: '비밀번호 불일치', desc: '두 비밀번호가 일치하지 않습니다.' });
      return;
    }
    setLoading(true);
    try {
      await AuthService.resetPassword(email, code, password);
      await alertModal({
        title: '재설정 완료',
        desc: '비밀번호가 변경되었습니다. 새 비밀번호로 로그인해 주세요.',
      });
      navigate('/login', { replace: true });
    } catch (error) {
      await alertModal({
        title: '재설정 실패',
        desc: error?.message || '인증 코드가 올바르지 않거나 만료되었습니다.',
      });
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
        {step === 'email' ? (
          <form className="modern-form" onSubmit={handleSendCode}>
            <div className="input-group-modern">
              <label htmlFor="fp-email">EMAIL</label>
              <input
                id="fp-email"
                type="email"
                placeholder="name@example.com"
                required
                className="input-modern"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
            <div className="auth-actions">
              <button type="submit" className="btn-modern btn-modern-primary full-width" disabled={loading}>
                {loading ? 'SENDING...' : 'SEND CODE'}
              </button>
              <div className="auth-links">
                <Link to="/login" className="link-text">BACK TO SIGN IN</Link>
              </div>
            </div>
          </form>
        ) : (
          <form className="modern-form" onSubmit={handleReset}>
            <div className="input-group-modern">
              <label htmlFor="fp-code">VERIFICATION CODE</label>
              <input
                id="fp-code"
                type="text"
                inputMode="numeric"
                placeholder="이메일로 받은 코드"
                required
                className="input-modern"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/[^0-9]/g, ''))}
                autoComplete="one-time-code"
              />
            </div>
            <div className="input-group-modern">
              <label htmlFor="fp-pw">NEW PASSWORD</label>
              <input
                id="fp-pw"
                type="password"
                placeholder="영문+숫자+특수문자 8자 이상"
                required
                className="input-modern"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <div className="input-group-modern">
              <label htmlFor="fp-pw2">CONFIRM PASSWORD</label>
              <input
                id="fp-pw2"
                type="password"
                placeholder="새 비밀번호 확인"
                required
                className="input-modern"
                value={password2}
                onChange={(e) => setPassword2(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <div className="auth-actions">
              <button type="submit" className="btn-modern btn-modern-primary full-width" disabled={loading}>
                {loading ? 'RESETTING...' : 'RESET PASSWORD'}
              </button>
              <div className="auth-links">
                <button type="button" className="link-text" onClick={() => setStep('email')}>
                  RESEND CODE
                </button>
                <span className="divider">/</span>
                <Link to="/login" className="link-text">BACK TO SIGN IN</Link>
              </div>
            </div>
          </form>
        )}
      </div>
      {confirmModal}
    </div>
  );
};

export default ForgotPassword;
