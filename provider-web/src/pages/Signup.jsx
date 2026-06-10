import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthService from '../services/auth/AuthService';
import ConsentSection from '../components/ConsentSection';
import { useConfirm } from '../hooks/useConfirm';
import './Signup.css';

// P4 (2026-06-08) — 출시 빌드에서는 자동 차단.
// VITE_PREVIEW_MODE=true (개발/스테이지) 일 때만 게스트 진입 허용.
// 운영 빌드(MODE='production') 에서는 button 자체 미렌더 + 함수 호출도 무효화.
const ALLOW_GUEST = (
  import.meta.env.VITE_PREVIEW_MODE === 'true' &&
  import.meta.env.MODE !== 'production'
);

function enterAsGuest(navigate) {
  if (!ALLOW_GUEST) return;   // 운영 빌드 안전망
  localStorage.setItem('pathwave_token', 'preview-mode-fake-token');
  localStorage.setItem('pathwave_user', JSON.stringify({
    id: 0, email: 'guest@dev.local', name: '게스트',
  }));
  navigate('/dashboard', { replace: true });
}

const Signup = () => {
  const navigate = useNavigate();
  const { alert: alertModal, modal: confirmModal } = useConfirm();
  const [formData, setFormData] = useState({
    companyName: '',
    businessNo: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: '',
    managerName: '',
    managerPhone: '',
    managerEmail: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [consents, setConsents] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      await alertModal({ title: '비밀번호 불일치', desc: '비밀번호와 확인 비밀번호가 일치하지 않습니다.' });
      return;
    }
    setIsLoading(true);

    try {
      // 동의 항목을 백엔드 형식으로 변환
      const consentsPayload = Object.entries(consents).map(([kind, accepted]) => ({
        kind, accepted: !!accepted, version: 'unspecified',
      }));
      await AuthService.register({ ...formData, consents: consentsPayload });
      await alertModal({ title: '회원가입 완료', desc: '대시보드로 이동합니다.' });
      navigate('/dashboard');
    } catch (error) {
      const msg = error?.message || '회원가입에 실패했습니다.';
      await alertModal({ title: '회원가입 실패', desc: msg });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="signup-container">
      <div className="signup-box">
        <div className="signup-header">
          <div className="logo-icon-large">P</div>
          <h2>매장 등록</h2>
          <p>PathWave 서비스를 운영할 매장을 등록합니다</p>
        </div>
        
        <form onSubmit={handleSignup} className="signup-form">
          <div className="form-section">
            <h3>사업자 정보</h3>
            <div className="form-grid">
              <div className="form-group">
                <label>업체명 (상호)</label>
                <input 
                  type="text" name="companyName" className="input-field" 
                  placeholder="예: 패스웨이브 커피" value={formData.companyName}
                  onChange={handleChange} required 
                />
              </div>
              <div className="form-group">
                <label>사업자 등록번호</label>
                <input 
                  type="text" name="businessNo" className="input-field" 
                  placeholder="000-00-00000" value={formData.businessNo}
                  onChange={handleChange} required 
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>계정 정보</h3>
            <div className="form-group">
              <label>로그인 이메일</label>
              <input 
                type="email" name="email" className="input-field" 
                placeholder="admin@example.com" value={formData.email}
                onChange={handleChange} required 
              />
            </div>
            <div className="form-grid">
              <div className="form-group">
                <label>비밀번호</label>
                <input 
                  type="password" name="password" className="input-field" 
                  placeholder="8자 이상" value={formData.password}
                  onChange={handleChange} required 
                />
              </div>
              <div className="form-group">
                <label>비밀번호 확인</label>
                <input 
                  type="password" name="confirmPassword" className="input-field" 
                  placeholder="재입력" value={formData.confirmPassword}
                  onChange={handleChange} required 
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>담당자 정보</h3>
            <div className="form-group">
              <label>담당자 성함</label>
              <input 
                type="text" name="managerName" className="input-field" 
                placeholder="실명을 입력해 주세요" value={formData.managerName}
                onChange={handleChange} required 
              />
            </div>
            <div className="form-grid">
              <div className="form-group">
                <label>담당자 연락처</label>
                <input 
                  type="tel" name="managerPhone" className="input-field" 
                  placeholder="010-0000-0000" value={formData.managerPhone}
                  onChange={handleChange} required 
                />
              </div>
              <div className="form-group">
                <label>담당자 이메일</label>
                <input 
                  type="email" name="managerEmail" className="input-field" 
                  placeholder="manager@example.com" value={formData.managerEmail}
                  onChange={handleChange} required 
                />
              </div>
            </div>
          </div>
          
          <ConsentSection
            subType="facility"
            value={consents}
            onChange={setConsents}
          />

          <button type="submit" className="btn-primary signup-btn" disabled={isLoading}>
            {isLoading ? '가입 신청 중...' : '가입 신청하기'}
          </button>
        </form>
        
        {/* P4 (2026-06-08) — 운영 빌드에서는 게스트 영역 자체 미렌더. */}
        {ALLOW_GUEST && (
          <div className="signup-guest">
            <button
              type="button"
              className="btn-guest"
              onClick={() => enterAsGuest(navigate)}
            >
              로그인 없이 이용
            </button>
          </div>
        )}
      </div>
      {confirmModal}
    </div>
  );
};

export default Signup;
