import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, X, Info } from 'lucide-react';
import AuthService from '../services/auth/AuthService';
import NotificationPreferencesService from '../services/notification/NotificationPreferencesService';
import ConfirmModal from '../components/common/ConfirmModal';
import { useDialog } from '../components/common/DialogProvider';
import PasswordInput from '../components/common/PasswordInput';
import StatusBadge from '../components/common/StatusBadge';
import BusinessInfoModal from '../components/common/BusinessInfoModal';
import './Settings.css';

/* ── 기본값 ── */
const DEFAULT_SETTINGS = {
  autoLogin: true,
  notificationsEnabled: true,
  benefitNotif: true,
  marketingNotif: false,
  nightAdNotif: true,
  // 운영 — 영업시간 외 푸시 알림 (OOT)
  ootPush: false,
};

/* ── 영업시간 mock — 실제 GET /api/facility/business-hours 로 대체 예정 ── */
const MOCK_BUSINESS_HOURS = {
  weekday: '10:00 ~ 22:00',
  weekend: '10:00 ~ 23:00',
  holiday: '휴무',
};

/* ── 승인 워크플로우 mock — 실제 GET 응답으로 대체 예정 ──
   사업자 정보 변경: status ∈ { null, 'requested', 'reviewing', 'approved', 'rejected' }
   회원 탈퇴:        status ∈ { null, 'requested', 'reviewing', 'completed', 'grace_period' } */
const WORKFLOW_BIZ_STATUS = {
  requested:  { label: '요청중',     badgeStatus: 'submitted' },
  reviewing:  { label: '검토중',     badgeStatus: 'review' },
  approved:   { label: '승인완료',   badgeStatus: 'active' },
  rejected:   { label: '반려',       badgeStatus: 'rejected', mode: 'admin' },
};
const WORKFLOW_WITHDRAW_STATUS = {
  requested:    { label: '탈퇴요청',     badgeStatus: 'submitted' },
  reviewing:    { label: '검토중',       badgeStatus: 'review' },
  completed:    { label: '탈퇴완료',     badgeStatus: 'active' },
  grace_period: { label: '재가입대기',   badgeStatus: 'paused' },
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

/* BusinessInfoModal 은 components/common/BusinessInfoModal.jsx 로 추출 (2026-05-10).
   결제관리에서도 동일 모달을 띄우기 위해 분리. */

/* ═══════════════════════════════════════════════════
   Main Settings Component
   ═══════════════════════════════════════════════════ */
const Settings = () => {
  const navigate = useNavigate();
  const { alert } = useDialog();
  const [settings, setSettings] = useState(loadSettings);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showBusinessModal, setShowBusinessModal] = useState(false);
  const [showWithdrawConfirm, setShowWithdrawConfirm] = useState(false);
  const [showWithdrawSuccess, setShowWithdrawSuccess] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  // 워크플로우 mock 상태 — 실서비스에선 GET /api/account/business-info/change-request/latest 등
  const [bizChangeStatus] = useState(null);     // 'requested' | 'reviewing' | ... | null
  const [withdrawStatus] = useState(null);      // 'requested' | ... | null

  const businessHours = MOCK_BUSINESS_HOURS;

  // 설정 변경 시 localStorage 자동 저장
  useEffect(() => {
    saveSettings(settings);
  }, [settings]);

  // ── Phase L — 백엔드 알림 카테고리 prefs (sub_type='facility') ───────────
  const [serverPrefs, setServerPrefs]     = useState(null);
  const [serverPrefsError, setServerErr]  = useState(null);
  const [togglingCategory, setToggling]   = useState(null);

  useEffect(() => {
    NotificationPreferencesService.list()
      .then(res => setServerPrefs(res.preferences || []))
      .catch(err => setServerErr(err.message || '알림 설정을 불러오지 못했습니다.'));
  }, []);

  const toggleServerPref = async (cat, next) => {
    setToggling(cat);
    // optimistic
    setServerPrefs(prev =>
      prev?.map(p => p.category === cat ? { ...p, enabled: next } : p));
    try {
      await NotificationPreferencesService.set(cat, next);
    } catch (err) {
      // rollback
      setServerPrefs(prev =>
        prev?.map(p => p.category === cat ? { ...p, enabled: !next } : p));
      alert(err.message || '변경 실패 — 잠시 후 다시 시도해 주세요.');
    } finally {
      setToggling(null);
    }
  };

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

  // 탈퇴는 슈퍼어드민 승인 후 처리 (사용자 요구 2026-05-11).
  // 즉시 로그아웃 / 계정 삭제 X. 요청 큐에 등록만 하고 사용자는 페이지 사용 계속 가능.
  const handleWithdraw = () => {
    // mock: 슈퍼어드민 audit 큐에 탈퇴 요청 등록.
    // 실서비스: POST /api/account/withdrawal/request
    try {
      const queue = JSON.parse(localStorage.getItem('pathwave_audit_queue') || '[]');
      queue.push({
        ts: new Date().toISOString(),
        action: 'account_withdraw_request',
        actor: AuthService.getCurrentUser()?.id || AuthService.getCurrentUser()?.email || 'unknown',
      });
      localStorage.setItem('pathwave_audit_queue', JSON.stringify(queue));
    } catch { /* ignore */ }
    setShowWithdrawConfirm(false);
    setShowWithdrawSuccess(true);
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

        {/* ════════════════════════════════════════════════════
            계정 (로그인 관련)
            ════════════════════════════════════════════════════ */}
        <h2 className="settings-group-title">계정</h2>
        <div className="settings-section">
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">자동로그인</span>
              <span className="settings-row-hint">다음 접속 시 로그인 정보를 유지합니다.</span>
            </div>
            <ToggleSwitch
              id="auto-login"
              checked={settings.autoLogin}
              onChange={() => toggleSetting('autoLogin')}
            />
          </div>

          <div className="settings-row clickable" onClick={() => setShowPasswordModal(true)}>
            <div className="settings-row-left">
              <span className="settings-row-label">비밀번호 변경</span>
            </div>
            <ChevronRight size={18} className="settings-row-arrow" />
          </div>
        </div>

        {/* ════════════════════════════════════════════════════
            운영 설정 (시설 운영 관련 — 시설관리자 전용)
            ════════════════════════════════════════════════════ */}
        <h2 className="settings-group-title">운영 설정</h2>
        <div className="settings-section">
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">영업시간</span>
              <span className="settings-row-desc">
                평일 {businessHours.weekday}<br/>
                주말 {businessHours.weekend} · 공휴일 {businessHours.holiday}
              </span>
            </div>
            <ChevronRight size={18} className="settings-row-arrow" />
          </div>

          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">영업시간 외 푸시 알림</span>
              <span className="settings-row-hint">영업시간이 아닌 시간대에는 고객 푸시 알림이 발송되지 않습니다.</span>
            </div>
            <ToggleSwitch
              id="oot-push"
              checked={settings.ootPush}
              onChange={() => toggleSetting('ootPush')}
            />
          </div>
        </div>

        {/* ════════════════════════════════════════════════════
            Phase L — 수신 알림 카테고리 (서버 동기, 매장 운영용)
            ════════════════════════════════════════════════════ */}
        <h2 className="settings-group-title">수신 알림 카테고리</h2>
        <div className="settings-section">
          {serverPrefsError && (
            <div className="settings-row">
              <div className="settings-row-left">
                <span className="settings-row-label" style={{ color: 'var(--pw-error, #ef4444)' }}>
                  {serverPrefsError}
                </span>
              </div>
            </div>
          )}
          {!serverPrefsError && !serverPrefs && (
            <div className="settings-row">
              <div className="settings-row-left">
                <span className="settings-row-hint">알림 설정을 불러오는 중…</span>
              </div>
            </div>
          )}
          {serverPrefs && serverPrefs.map((p) => (
            <div className="settings-row" key={p.category}>
              <div className="settings-row-left">
                <span className="settings-row-label">{p.label}</span>
              </div>
              <ToggleSwitch
                id={`server-pref-${p.category}`}
                checked={p.enabled}
                onChange={() => togglingCategory !== p.category
                  && toggleServerPref(p.category, !p.enabled)}
              />
            </div>
          ))}
        </div>

        {/* ════════════════════════════════════════════════════
            알림 설정 (시설관리자가 받는 알림 환경)
            ════════════════════════════════════════════════════ */}
        <h2 className="settings-group-title">알림 설정</h2>
        <div className="settings-section">
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">알림 수신</span>
              <span className="settings-row-hint">시스템 점검 및 긴급 알림은 설정과 관계없이 발송됩니다.</span>
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
                  <span className="settings-row-label">혜택 알림</span>
                  <span className="settings-row-hint">내주변(위치기반)의 혜택 알림 받기</span>
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
                  <span className="settings-row-hint">서비스 혜택 등록 시 모든 알림 받기</span>
                </div>
                <ToggleSwitch
                  id="marketing-notif"
                  checked={settings.marketingNotif}
                  onChange={() => toggleSetting('marketingNotif')}
                />
              </div>

              <div className="settings-row">
                <div className="settings-row-left">
                  <span className="settings-row-label">야간 광고성 알림</span>
                  <span className="settings-row-hint">21:00 ~ 08:00 사이 알림 차단</span>
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

        {/* ════════════════════════════════════════════════════
            계정 관리 (사업자 정보 / 탈퇴 — 슈퍼어드민 승인 워크플로)
            ════════════════════════════════════════════════════ */}
        <h2 className="settings-group-title">계정 관리</h2>
        <div className="settings-section">
          <div className="settings-row clickable" onClick={() => setShowBusinessModal(true)}>
            <div className="settings-row-left">
              <span className="settings-row-label">사업자 정보 변경</span>
              <span className="settings-row-hint">슈퍼어드민 승인 후 반영됩니다.</span>
            </div>
            <div className="settings-row-meta">
              {bizChangeStatus && WORKFLOW_BIZ_STATUS[bizChangeStatus] && (
                <StatusBadge
                  status={WORKFLOW_BIZ_STATUS[bizChangeStatus].badgeStatus}
                  label={WORKFLOW_BIZ_STATUS[bizChangeStatus].label}
                  mode={WORKFLOW_BIZ_STATUS[bizChangeStatus].mode || 'provider'}
                  size="sm"
                />
              )}
              <ChevronRight size={18} className="settings-row-arrow" />
            </div>
          </div>

          <div className="settings-row clickable" onClick={() => setShowWithdrawConfirm(true)}>
            <div className="settings-row-left">
              <span className="settings-row-label">회원 탈퇴</span>
              <span className="settings-row-hint">탈퇴 요청 후 슈퍼어드민 검토를 거칩니다.</span>
            </div>
            <div className="settings-row-meta">
              {withdrawStatus && WORKFLOW_WITHDRAW_STATUS[withdrawStatus] && (
                <StatusBadge
                  status={WORKFLOW_WITHDRAW_STATUS[withdrawStatus].badgeStatus}
                  label={WORKFLOW_WITHDRAW_STATUS[withdrawStatus].label}
                  size="sm"
                />
              )}
              <ChevronRight size={18} className="settings-row-arrow" />
            </div>
          </div>
        </div>

        <div className="settings-workflow-hint">
          <Info size={14} />
          <span>사업자 정보 변경 / 회원 탈퇴는 슈퍼어드민 검토 후 처리됩니다. 진행 상태는 알림으로 안내됩니다.</span>
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
          ※ PathWave는 서비스 플랫폼으로, 플랫폼 내에서 제공되는 정보 및 이벤트, 혜택 등에 대한 책임은 등록 업체에 있습니다.
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

      {/* 탈퇴 요청 — 슈퍼어드민 승인 후 처리 (즉시 로그아웃 X) */}
      {showWithdrawConfirm && (
        <ConfirmModal
          isOpen={true}
          title="회원 탈퇴 요청"
          desc={'회원 탈퇴는 슈퍼어드민 검토를 거쳐 처리됩니다.\n탈퇴 요청을 보내시겠습니까?\n\n※ 미정산 결제건이 있으면 정산 완료 후 처리됩니다.'}
          confirmText="요청하기"
          onConfirm={handleWithdraw}
          onCancel={() => setShowWithdrawConfirm(false)}
        />
      )}

      {showWithdrawSuccess && (
        <ConfirmModal
          isOpen={true}
          singleButton
          title="탈퇴 요청이 접수되었습니다"
          desc={'슈퍼어드민 검토 후 결과를 알림으로 안내드립니다.\n검토 중에는 서비스를 그대로 사용하실 수 있습니다.'}
          confirmText="확인"
          onConfirm={() => setShowWithdrawSuccess(false)}
          onCancel={() => setShowWithdrawSuccess(false)}
        />
      )}
    </>
  );
};

export default Settings;
