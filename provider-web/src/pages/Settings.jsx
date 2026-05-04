import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import AuthService from '../services/auth/AuthService';
import ConfirmModal from '../components/common/ConfirmModal';
import PasswordInput from '../components/common/PasswordInput';
import './Settings.css';

/* ── 기본값 ── */
const DEFAULT_SETTINGS = {
  autoLogin: true,
  notificationsEnabled: true,
  benefitNotif: true,
  marketingNotif: false,
  nightAdNotif: true,
};

const STORAGE_KEY = 'pathwave_settings';

/* ── localStorage 헬퍼 ── */
const loadSettings = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? { ...DEFAULT_SETTINGS, ...JSON.parse(stored) } : { ...DEFAULT_SETTINGS };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
};

const saveSettings = (settings) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
};

/* ── Toggle Switch Component ── */
const ToggleSwitch = ({ checked, onChange, id }) => (
  <label className="toggle-switch" htmlFor={id}>
    <input type="checkbox" id={id} checked={checked} onChange={onChange} />
    <div className="toggle-track" />
    <div className="toggle-thumb" />
    <span className="toggle-text">{checked ? 'ON' : 'OFF'}</span>
  </label>
);

/* ── Password Change Modal ── */
const PasswordModal = ({ onClose }) => {
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = () => {
    setError('');

    if (!currentPw) {
      setError('현재 비밀번호를 입력해주세요.');
      return;
    }
    if (newPw.length < 8) {
      setError('새 비밀번호는 8자 이상이어야 합니다.');
      return;
    }
    if (newPw !== confirmPw) {
      setError('새 비밀번호가 일치하지 않습니다.');
      return;
    }
    if (currentPw === newPw) {
      setError('현재 비밀번호와 다른 비밀번호를 입력해주세요.');
      return;
    }

    // TODO: AuthService.changePassword() API 호출
    setSuccess(true);
    setTimeout(() => onClose(), 1500);
  };

  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-modal-header">
          <h2 className="settings-modal-title">비밀번호 변경</h2>
          <button className="settings-modal-close" onClick={onClose}><X size={20} /></button>
        </div>

        <div className="settings-modal-body">
        {success ? (
          <div style={{ textAlign: 'center', padding: 'var(--pw-space-8) 0', color: 'var(--pw-primary)', fontWeight: 600 }}>
            ✓ 비밀번호가 변경되었습니다.
          </div>
        ) : (
          <>
            <div className="settings-modal-field">
              <label className="settings-modal-label">현재 비밀번호</label>
              <PasswordInput
                placeholder="현재 비밀번호 입력"
                value={currentPw}
                onChange={e => setCurrentPw(e.target.value)}
                autoComplete="current-password"
              />
            </div>

            <div className="settings-modal-field">
              <label className="settings-modal-label">새 비밀번호</label>
              <PasswordInput
                placeholder="8자 이상 입력"
                value={newPw}
                onChange={e => setNewPw(e.target.value)}
                autoComplete="new-password"
              />
            </div>

            <div className="settings-modal-field">
              <label className="settings-modal-label">새 비밀번호 확인</label>
              <PasswordInput
                placeholder="새 비밀번호 재입력"
                value={confirmPw}
                onChange={e => setConfirmPw(e.target.value)}
                autoComplete="new-password"
              />
            </div>

            {error && <p className="settings-modal-error">{error}</p>}

            <div className="settings-modal-actions">
              <button className="settings-modal-btn cancel" onClick={onClose}>취소</button>
              <button className="settings-modal-btn confirm" onClick={handleSubmit}>변경</button>
            </div>
          </>
        )}
        </div>
      </div>
    </div>
  );
};

/* ── Business Info Modal ── */
const BusinessInfoModal = ({ onClose }) => {
  const user = AuthService.getCurrentUser();
  const [formData, setFormData] = useState({
    name: user?.name || '시원컴퍼니',
    bizNumber: '123-45-67890',
    phone: '02-1234-5678',
    email: user?.email || 'admin@pathwave.com',
  });
  const [success, setSuccess] = useState(false);

  const handleSave = () => {
    // TODO: 실제 API 호출로 사업자 정보 업데이트
    const updatedUser = { ...user, name: formData.name, email: formData.email };
    localStorage.setItem('pathwave_user', JSON.stringify(updatedUser));
    setSuccess(true);
    setTimeout(() => onClose(), 1500);
  };

  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-modal-header">
          <h2 className="settings-modal-title">사업자 정보 변경</h2>
          <button className="settings-modal-close" onClick={onClose}><X size={20} /></button>
        </div>

        <div className="settings-modal-body">
        {success ? (
          <div style={{ textAlign: 'center', padding: 'var(--pw-space-8) 0', color: 'var(--pw-primary)', fontWeight: 600 }}>
            ✓ 정보가 저장되었습니다.
          </div>
        ) : (
          <>
            <div className="settings-modal-field">
              <label className="settings-modal-label">대표자명</label>
              <input
                type="text"
                className="settings-modal-input"
                value={formData.name}
                onChange={e => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div className="settings-modal-field">
              <label className="settings-modal-label">사업자번호</label>
              <input
                type="text"
                className="settings-modal-input"
                value={formData.bizNumber}
                onChange={e => setFormData({ ...formData, bizNumber: e.target.value })}
                placeholder="000-00-00000"
              />
            </div>

            <div className="settings-modal-field">
              <label className="settings-modal-label">연락처</label>
              <input
                type="tel"
                className="settings-modal-input"
                value={formData.phone}
                onChange={e => setFormData({ ...formData, phone: e.target.value })}
                placeholder="02-0000-0000"
              />
            </div>

            <div className="settings-modal-field">
              <label className="settings-modal-label">이메일</label>
              <input
                type="email"
                className="settings-modal-input"
                value={formData.email}
                onChange={e => setFormData({ ...formData, email: e.target.value })}
              />
            </div>

            <div className="settings-modal-actions">
              <button className="settings-modal-btn cancel" onClick={onClose}>취소</button>
              <button className="settings-modal-btn confirm" onClick={handleSave}>저장</button>
            </div>
          </>
        )}
        </div>
      </div>
    </div>
  );
};

/* ═══════════════════════════════════════════════════
   Main Settings Component
   ═══════════════════════════════════════════════════ */
const Settings = () => {
  const navigate = useNavigate();
  const [settings, setSettings] = useState(loadSettings);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showBusinessModal, setShowBusinessModal] = useState(false);
  const [showWithdrawConfirm, setShowWithdrawConfirm] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  // 설정 변경 시 localStorage 자동 저장
  useEffect(() => {
    saveSettings(settings);
  }, [settings]);

  const toggleSetting = (key) => {
    setSettings(prev => {
      const next = { ...prev, [key]: !prev[key] };

      // 알림 설정 OFF → 하위 항목 모두 OFF
      if (key === 'notificationsEnabled' && !next.notificationsEnabled) {
        next.benefitNotif = false;
        next.marketingNotif = false;
        next.nightAdNotif = false;
      }
      // 알림 설정 ON → 기본값 복원
      if (key === 'notificationsEnabled' && next.notificationsEnabled) {
        next.benefitNotif = true;
        next.nightAdNotif = true;
      }

      return next;
    });
  };

  const handleLogout = async () => {
    await AuthService.logout();
    navigate('/login');
  };

  const handleWithdraw = async () => {
    // TODO: 실제 회원탈퇴 API 호출
    await AuthService.logout();
    navigate('/login');
  };

  return (
    <>
      {/* 모바일 전용 헤더 (CSS로 768px 이하에서만 표시) */}
      <header className="common-form-header settings-mobile-header">
        <button className="back-btn" onClick={() => navigate(-1)}>
          <ChevronLeft size={24} />
        </button>
        <h1>설정</h1>
      </header>

      {/* PC 전용 헤더 (CSS로 769px 이상에서만 표시) */}
      <div className="page-header-section settings-pc-header">
        <h1 className="page-title">설정</h1>
        <p className="sub-title">서비스 설정 및 계정 관리</p>
      </div>

      <div className="settings-page">

        {/* ── 서비스 설정 ── */}
        <div className="settings-section">
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">자동로그인 설정</span>
            </div>
            <ToggleSwitch
              id="auto-login"
              checked={settings.autoLogin}
              onChange={() => toggleSetting('autoLogin')}
            />
          </div>
        </div>

        {/* ── 알림 설정 ── */}
        <div className="settings-section">
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">알림설정</span>
              <span className="settings-row-desc">※ 시스템 점비 및 긴급알림은 설정과 관련없이 발송 됩니다.</span>
            </div>
            <ToggleSwitch
              id="notifications-enabled"
              checked={settings.notificationsEnabled}
              onChange={() => toggleSetting('notificationsEnabled')}
            />
          </div>

          {settings.notificationsEnabled && (
            <div className="settings-sub-items">
              <div className="settings-row">
                <div className="settings-row-left">
                  <span className="settings-row-label">혜택알림</span>
                  <span className="settings-row-desc">내주변(위치기반)의 혜택알림 받기</span>
                </div>
                <ToggleSwitch
                  id="benefit-notif"
                  checked={settings.benefitNotif}
                  onChange={() => toggleSetting('benefitNotif')}
                />
              </div>

              <div className="settings-row">
                <div className="settings-row-left">
                  <span className="settings-row-label">마케팅 알림</span>
                  <span className="settings-row-desc">서비스 혜택 등록 시 모든 알림 받기</span>
                </div>
                <ToggleSwitch
                  id="marketing-notif"
                  checked={settings.marketingNotif}
                  onChange={() => toggleSetting('marketingNotif')}
                />
              </div>

              <div className="settings-row">
                <div className="settings-row-left">
                  <span className="settings-row-label">야간 광고성 알림 수신</span>
                  <span className="settings-row-desc">21:00 ~ 08:00 사이까지 알림거부</span>
                </div>
                <ToggleSwitch
                  id="night-ad-notif"
                  checked={settings.nightAdNotif}
                  onChange={() => toggleSetting('nightAdNotif')}
                />
              </div>
            </div>
          )}
        </div>

        {/* ── 계정 관리 ── */}
        <div className="settings-section">
          <div className="settings-row clickable" onClick={() => setShowPasswordModal(true)}>
            <div className="settings-row-left">
              <span className="settings-row-label">비밀번호 변경</span>
            </div>
            <ChevronRight size={18} className="settings-row-arrow" />
          </div>

          <div className="settings-row clickable" onClick={() => setShowBusinessModal(true)}>
            <div className="settings-row-left">
              <span className="settings-row-label">사업자 정보 변경</span>
            </div>
            <ChevronRight size={18} className="settings-row-arrow" />
          </div>

          <div className="settings-row clickable" onClick={() => setShowWithdrawConfirm(true)}>
            <div className="settings-row-left">
              <span className="settings-row-label">회원탈퇴</span>
            </div>
            <ChevronRight size={18} className="settings-row-arrow" />
          </div>
        </div>



        {/* ── 로그아웃 ── */}
        <button className="settings-logout-btn" onClick={() => setShowLogoutConfirm(true)}>
          로그아웃
        </button>
      </div>

      {/* ── Footer (Full Width Dark) ── */}
      <div className="settings-footer">
        <div className="settings-footer-links">
          <button className="settings-footer-link">고객센터</button>
          <div className="settings-footer-divider" />
          <button className="settings-footer-link">자주묻는 질문</button>
          <div className="settings-footer-divider" />
          <button className="settings-footer-link">서비스이용약관</button>
        </div>
        <p className="settings-footer-notice">
          ※ BE서비스는 서비스플랫폼으로 플랫폼내에서 제공되는 정보 및 이벤트, 혜택 등…은 등록 업체에 책임이 있습니다.
        </p>
        <div className="settings-footer-company">
          <p style={{ fontWeight: 600, marginBottom: '2px' }}>시원컴퍼니 Copyright 2023, siwon company. All rights reserved.</p>
          <p>서울특별시 서초구 메헌로 26(하이브랜드 1312,1313층) 02-1234-5678</p>
        </div>
      </div>

      {/* ── Modals ── */}
      {showPasswordModal && (
        <PasswordModal onClose={() => setShowPasswordModal(false)} />
      )}

      {showBusinessModal && (
        <BusinessInfoModal onClose={() => setShowBusinessModal(false)} />
      )}

      {showLogoutConfirm && (
        <ConfirmModal
          isOpen={true}
          title="로그아웃"
          desc="로그아웃 하시겠습니까?"
          onConfirm={handleLogout}
          onCancel={() => setShowLogoutConfirm(false)}
        />
      )}

      {showWithdrawConfirm && (
        <ConfirmModal
          isOpen={true}
          title="회원탈퇴"
          desc="정말 탈퇴하시겠습니까? 모든 데이터가 삭제되며 복구할 수 없습니다."
          onConfirm={handleWithdraw}
          onCancel={() => setShowWithdrawConfirm(false)}
        />
      )}
    </>
  );
};

export default Settings;
