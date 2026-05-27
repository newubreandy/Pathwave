import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Plus, X, Mail, MoreVertical, Shield, UserCheck, Clock, AlertTriangle, ShieldAlert } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import StaffService, { ROLES, ROLE_LABELS, STATUS, STATUS_LABELS, validateEmail } from '../services/staff/StaffService';
import PwPageHeader from '../components/common/PwPageHeader';
import { useConfirm } from '../hooks/useConfirm';
import { MOCK_STAFF } from '../services/staff/mockStaff';
import ConfirmModal from '../components/common/ConfirmModal';
import PasswordInput from '../components/common/PasswordInput';
import BusinessInfoModal from '../components/common/BusinessInfoModal';
import './StaffManagement.css';

/* P5 (2026-05-26): 더미 회원/회사 데이터 ('호텔H' / '02-1234-5678' / 'hotel_H'
   / 'webmaster@hotelh.com' 등) 제거. 실 데이터는 가입 시 입력 + 백엔드 fetch.
   Phase 2+ 에서 GET /api/account/business-info 실연동 시 mock 자리 채움. */
const INITIAL_PROFILE = {
  company: {
    name: '',
    type: '',
    registrationNumber: '',
    registrationFile: '',
    ceoName: '',
    cellularPhone: '',
    officePhone: '',
    address: '',
  },
  agent: {
    name: '',
    phone: '',
  },
  account: {
    id: '',
    password: '',
    email: '',
  },
};

/* ── 역할 뱃지 ── */
const RoleBadge = ({ role }) => {
  const cls = `staff-role-badge role-${role.toLowerCase()}`;
  return <span className={cls}>{ROLE_LABELS[role]}</span>;
};

/* ── 상태 뱃지 ── */
const StatusBadge = ({ status, invitedAt }) => {
  const expired = status === STATUS.INVITED && StaffService.isInviteExpired(invitedAt);
  if (expired) {
    return <span className="staff-status-badge status-expired">만료</span>;
  }
  const cls = `staff-status-badge status-${status.toLowerCase()}`;
  return <span className={cls}>{STATUS_LABELS[status]}</span>;
};

/* ── 초대 모달 ── */
const InviteModal = ({ onClose, onInvite }) => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [role, setRole] = useState(ROLES.STAFF);
  const [emailError, setEmailError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const handleEmailBlur = () => {
    if (email.trim()) {
      const result = validateEmail(email);
      setEmailError(result.valid ? '' : result.error);
    }
  };

  const handleSubmit = async () => {
    const emailResult = validateEmail(email);
    if (!emailResult.valid) {
      setEmailError(emailResult.error);
      return;
    }
    if (!name.trim()) {
      setSubmitError('이름을 입력해 주세요.');
      return;
    }
    if (!phone.trim()) {
      setSubmitError('전화번호를 입력해 주세요.');
      return;
    }

    setIsLoading(true);
    setSubmitError('');
    try {
      await onInvite({ email, name, phone, role });
      onClose();
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal staff-invite-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-modal-header">
          <h3 className="settings-modal-title">{t('staff_mgmt.invite_btn')}</h3>
          <button className="settings-modal-close" onClick={onClose} aria-label="닫기"><X size={20} aria-hidden="true" /></button>
        </div>

        <div className="staff-invite-form">
          <div className="staff-invite-field">
            <label>{t('staff_mgmt.invite_email_label')} *</label>
            <input
              type="email"
              value={email}
              onChange={e => { setEmail(e.target.value); setEmailError(''); }}
              onBlur={handleEmailBlur}
              placeholder="example@email.com"
              className={emailError ? 'has-error' : ''}
            />
            {emailError && <span className="staff-field-error">{emailError}</span>}
          </div>

          <div className="staff-invite-field">
            <label>이름 *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="직원 이름"
            />
          </div>

          <div className="staff-invite-field">
            <label>전화번호 *</label>
            <input
              type="tel"
              value={phone}
              onChange={e => setPhone(e.target.value)}
              placeholder="010-0000-0000"
            />
          </div>

          <div className="staff-invite-field">
            <label>{t('staff_mgmt.role_label')}</label>
            <div className="staff-role-select">
              <button
                type="button"
                className={`role-option ${role === ROLES.MANAGER ? 'selected' : ''}`}
                onClick={() => setRole(ROLES.MANAGER)}
              >
                <Shield size={16} />
                <span>{t('staff_mgmt.role_admin')}</span>
                <small>매장안내/채팅/스탬프/쿠폰 제어</small>
              </button>
              <button
                type="button"
                className={`role-option ${role === ROLES.STAFF ? 'selected' : ''}`}
                onClick={() => setRole(ROLES.STAFF)}
              >
                <UserCheck size={16} />
                <span>{t('staff_mgmt.role_staff')}</span>
                <small>매장안내/채팅/스탬프/쿠폰 제어</small>
              </button>
            </div>
          </div>

          {submitError && (
            <div className="staff-submit-error">
              <AlertTriangle size={14} /> {submitError}
            </div>
          )}

          <div className="staff-invite-note">
            <Mail size={14} />
            <span>{t('staff_mgmt.invite_expires_hint')}</span>
          </div>
        </div>

        <div className="settings-modal-actions">
          <button className="settings-modal-btn cancel" onClick={onClose}>취소</button>
          <button className="settings-modal-btn confirm" onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? '발송 중...' : t('staff_mgmt.invite_btn')}
          </button>
        </div>
      </div>
    </div>
  );
};

/* ── 직원 상세/액션 모달 ── */
const StaffActionModal = ({ member, onClose, onRoleChange, onDisable, onRemove, onResend }) => {
  const { t } = useTranslation();
  const isOwner = member.role === ROLES.OWNER;
  const isInvited = member.status === STATUS.INVITED;
  const isExpired = isInvited && StaffService.isInviteExpired(member.invitedAt);

  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal staff-action-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-modal-header">
          <h3 className="settings-modal-title">{t('staff_mgmt.title')}</h3>
          <button className="settings-modal-close" onClick={onClose} aria-label="닫기"><X size={20} aria-hidden="true" /></button>
        </div>

        <div className="staff-action-info">
          <div className="staff-action-name">{member.name}</div>
          <div className="staff-action-email">{member.email}</div>
          <div className="staff-action-badges">
            <RoleBadge role={member.role} />
            <StatusBadge status={member.status} invitedAt={member.invitedAt} />
          </div>
        </div>

        <div className="staff-action-list">
          {!isOwner && member.status === STATUS.ACTIVE && (
            <>
              <div className="staff-action-label">{t('staff_mgmt.role_label')} 변경</div>
              <div className="staff-role-change">
                <button
                  className={`role-change-btn ${member.role === ROLES.MANAGER ? 'active' : ''}`}
                  onClick={() => onRoleChange(member.id, ROLES.MANAGER)}
                >
                  {t('staff_mgmt.role_admin')}
                </button>
                <button
                  className={`role-change-btn ${member.role === ROLES.STAFF ? 'active' : ''}`}
                  onClick={() => onRoleChange(member.id, ROLES.STAFF)}
                >
                  {t('staff_mgmt.role_staff')}
                </button>
              </div>
            </>
          )}

          {isInvited && (
            <button className="staff-action-btn" onClick={() => onResend(member.id)} aria-label="초대 메일 재발송">
              <Mail size={16} />
              {isExpired
                ? `${t('staff_mgmt.invite_resend')} (${t('staff_mgmt.status_expired')})`
                : t('staff_mgmt.invite_resend')}
            </button>
          )}

          {isInvited && (
            <button className="staff-action-btn warn" onClick={() => onRemove(member.id)}>
              {t('staff_mgmt.invite_revoke')}
            </button>
          )}

          {!isOwner && member.status === STATUS.ACTIVE && (
            <button className="staff-action-btn warn" onClick={() => onDisable(member.id)}>
              비활성화
            </button>
          )}

          {!isOwner && member.status !== STATUS.INVITED && (
            <button className="staff-action-btn danger" onClick={() => onRemove(member.id)}>
              삭제
            </button>
          )}

          {isOwner && (
            <div className="staff-action-note">대표는 역할 변경/삭제가 불가합니다.</div>
          )}
        </div>
      </div>
    </div>
  );
};

/* ── 회원정보 편집 모달 ── */
const EditModal = ({ title, fields, onClose, onSave }) => {
  const [values, setValues] = useState(
    fields.reduce((acc, f) => ({ ...acc, [f.key]: f.value }), {})
  );

  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-modal-header">
          <h3 className="settings-modal-title">{title}</h3>
          <button className="settings-modal-close" onClick={onClose} aria-label="닫기"><X size={20} aria-hidden="true" /></button>
        </div>
        <div className="settings-modal-body">
          {fields.map(f => (
            <div key={f.key} className="settings-modal-field">
              <label className="settings-modal-label">{f.label}</label>
              {f.type === 'password' ? (
                <PasswordInput
                  value={values[f.key]}
                  onChange={e => setValues(prev => ({ ...prev, [f.key]: e.target.value }))}
                  disabled={f.disabled}
                />
              ) : (
                <input
                  className="settings-modal-input"
                  type={f.type || 'text'}
                  value={values[f.key]}
                  onChange={e => setValues(prev => ({ ...prev, [f.key]: e.target.value }))}
                  disabled={f.disabled}
                />
              )}
            </div>
          ))}
          <div className="settings-modal-actions">
            <button className="settings-modal-btn cancel" onClick={onClose}>취소</button>
            <button className="settings-modal-btn confirm" onClick={() => onSave(values)}>저장</button>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ── 회원정보 탭 (Settings.jsx와 동일한 디자인 패턴) ── */
const ProfileTab = () => {
  const [data] = useState(INITIAL_PROFILE);
  // 사용자 요구 (2026-05-11): [변경하기] 클릭 시 BusinessInfoModal(사업자 정보 변경)
  // 모달 노출 — 슈퍼어드민 승인 큐로 변경 요청 진입. (이전 ConfirmModal 안내 → 정식 모달로)
  const [showBusinessModal, setShowBusinessModal] = useState(false);

  return (
    <>
      <div className="staff-content">
        <div className="settings-section">
          {/* 섹션 헤더: 회사정보 + 변경하기 */}
          <div className="settings-row profile-section-header">
            <div className="settings-row-left">
              <span className="settings-row-label profile-section-title">회사정보</span>
            </div>
            <button className="profile-edit-btn" onClick={() => setShowBusinessModal(true)}>
              변경하기
            </button>
          </div>

          {/* 회사정보 */}
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">상호</span>
              <span className="settings-row-desc">{data.company.name}</span>
            </div>
          </div>
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">사업자 유형</span>
              <span className="settings-row-desc">{data.company.type}</span>
            </div>
          </div>
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">사업자등록번호</span>
              <span className="settings-row-desc">{data.company.registrationNumber}</span>
            </div>
          </div>
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">대표자</span>
              <span className="settings-row-desc">{data.company.ceoName}</span>
            </div>
          </div>
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">대표 연락처</span>
              <span className="settings-row-desc">{data.company.cellularPhone} / {data.company.officePhone}</span>
            </div>
          </div>
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">주소</span>
              <span className="settings-row-desc">{data.company.address}</span>
            </div>
          </div>

          {/* 계정정보 */}
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">계정 ID</span>
              <span className="settings-row-desc">{data.account.id}</span>
            </div>
          </div>
          <div className="settings-row">
            <div className="settings-row-left">
              <span className="settings-row-label">이메일</span>
              <span className="settings-row-desc">{data.account.email}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 사업자 정보 변경 모달 — 결제관리 [이메일 변경] 진입점도 이 페이지로 navigate 후
          [변경하기] 클릭으로 동일 모달 진입. (사용자 요구 2026-05-11) */}
      {showBusinessModal && (
        <BusinessInfoModal onClose={() => setShowBusinessModal(false)} />
      )}
    </>
  );
};

/* ══════════════════════════════════════════════
   Main Component — 탭 통합 (회원정보 + 직원관리)
   ══════════════════════════════════════════════ */
const StaffManagement = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { alert: alertModal, modal: confirmModalEl } = useConfirm();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'staff';

  const setActiveTab = (tab) => {
    if (tab === 'staff') {
      searchParams.delete('tab');
    } else {
      searchParams.set('tab', tab);
    }
    setSearchParams(searchParams);
  };

  const [staffList, setStaffList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showInvite, setShowInvite] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [confirmModal, setConfirmModal] = useState(null);

  const loadStaff = useCallback(async () => {
    // P5 후속 (2026-05-27): MOCK_STAFF 제거 — 실 백엔드 호출.
    // 백엔드 미연동 환경에서는 빈 배열 (직원 초대 화면으로 안내).
    setIsLoading(true);
    try {
      // TODO: StaffService.list() 실연동 — 백엔드 enpoint 확정 후
      // const res = await StaffService.list();
      // const items = res?.staffs || res?.data || res || [];
      // setStaffList(Array.isArray(items) ? items : []);
      setStaffList([]);
    } catch (err) {
      console.error('Failed to load staff', err);
      setStaffList([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStaff();
  }, [loadStaff]);

  const handleInvite = async (formData) => {
    await StaffService.inviteStaff('store_1', formData);
    await loadStaff();
  };

  const handleRoleChange = async (id, newRole) => {
    try {
      await StaffService.updateRole(id, newRole);
      await loadStaff();
      setSelectedMember(null);
    } catch (err) {
      await alertModal({ title: '오류', desc: err.message });
    }
  };

  const handleDisable = (id) => {
    setConfirmModal({
      title: '직원 비활성화',
      message: '해당 직원을 비활성화하시겠습니까?\n비활성화된 직원은 서비스에 접근할 수 없습니다.',
      onConfirm: async () => {
        try {
          await StaffService.disableStaff(id);
          await loadStaff();
          setSelectedMember(null);
        } catch (err) {
          await alertModal({ title: '오류', desc: err.message });
        }
        setConfirmModal(null);
      },
    });
  };

  const handleRemove = (id) => {
    setConfirmModal({
      title: '직원 삭제',
      message: '해당 직원을 삭제하시겠습니까?\n삭제된 직원은 복구할 수 없습니다.',
      onConfirm: async () => {
        try {
          await StaffService.removeStaff(id);
          await loadStaff();
          setSelectedMember(null);
        } catch (err) {
          await alertModal({ title: '오류', desc: err.message });
        }
        setConfirmModal(null);
      },
    });
  };

  const handleResend = async (id) => {
    try {
      await StaffService.resendInvite(id);
      await loadStaff();
      setSelectedMember(null);
      await alertModal({ title: '재발송 완료', desc: '초대 메일이 재발송되었습니다.' });
    } catch (err) {
      await alertModal({ title: '오류', desc: err.message });
    }
  };

  const activeCount = staffList.filter(s => s.status === STATUS.ACTIVE).length;
  const invitedCount = staffList.filter(s => s.status === STATUS.INVITED).length;

  return (
    <div className="common-form-page">
      {/* 공통 헤더 — PwPageHeader (2026-05-27 통일) */}
      <PwPageHeader
        title={activeTab === 'staff' ? t('staff_mgmt.title') : '회원정보'}
      />

      <div className="staff-tabs">
        <button
          className={`staff-tab ${activeTab === 'staff' ? 'active' : ''}`}
          onClick={() => setActiveTab('staff')}
        >
          직원관리
        </button>
        <button
          className={`staff-tab ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          회원정보
        </button>
      </div>

      {/* ── 회원정보 탭 ── */}
      {activeTab === 'profile' && <ProfileTab />}

      {/* ── 직원관리 탭 ── */}
      {activeTab === 'staff' && (
        <div className="staff-content">
          {/* 요약 + 초대 버튼 */}
          <div className="staff-summary-bar">
            <div className="staff-counts">
              <span className="staff-count-item">
                <span className="staff-count-num">{activeCount}</span>
                <span className="staff-count-label">{t('staff_mgmt.status_accepted')}</span>
              </span>
              <span className="staff-count-divider" />
              <span className="staff-count-item">
                <span className="staff-count-num">{invitedCount}</span>
                <span className="staff-count-label">{t('staff_mgmt.status_pending')}</span>
              </span>
            </div>
            <button className="staff-invite-btn" onClick={() => setShowInvite(true)} aria-label="직원 초대">
              <Plus size={18} />
              <span>{t('staff_mgmt.invite_btn')}</span>
            </button>
          </div>

          {/* 직원 목록 */}
          {isLoading ? (
            <div className="staff-loading">불러오는 중...</div>
          ) : staffList.length === 0 ? (
            <div className="staff-empty">
              <UserCheck size={40} strokeWidth={1} />
              <p>등록된 직원이 없습니다.</p>
              <button className="staff-empty-btn" onClick={() => setShowInvite(true)}>
                {t('staff_mgmt.invite_btn')}
              </button>
            </div>
          ) : (
            <div className="staff-list">
              {staffList.map(member => {
                const isExpired = member.status === STATUS.INVITED && StaffService.isInviteExpired(member.invitedAt);
                return (
                  <div
                    key={member.id}
                    className={`staff-card ${member.status === STATUS.DISABLED ? 'disabled' : ''}`}
                    onClick={() => setSelectedMember(member)}
                  >
                    <div className="staff-card-left">
                      <div className="staff-avatar">
                        {member.name.charAt(0)}
                      </div>
                      <div className="staff-card-info">
                        <div className="staff-card-name">
                          {member.name}
                          <RoleBadge role={member.role} />
                        </div>
                        <div className="staff-card-email">{member.email}</div>
                        {member.status === STATUS.INVITED && (
                          <div className={`staff-card-invited ${isExpired ? 'expired' : ''}`}>
                            <Clock size={12} />
                            {isExpired ? '초대 만료' : `초대 발송 ${member.invitedAt}`}
                          </div>
                        )}
                      </div>
                    </div>
                    <button className="staff-card-action" onClick={(e) => { e.stopPropagation(); setSelectedMember(member); }} aria-label="직원 작업 더 보기">
                      <MoreVertical size={18} />
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {/* 권한 안내 */}
          <div className="staff-permission-info">
            <h3>역할별 권한 안내</h3>
            <div className="staff-perm-grid">
              <div className="staff-perm-col">
                <div className="staff-perm-role"><RoleBadge role={ROLES.OWNER} /> 대표</div>
                <ul>
                  <li>모든 기능 제어 가능</li>
                  <li>직원 초대/관리</li>
                  <li>결제/사업자정보 관리</li>
                </ul>
              </div>
              <div className="staff-perm-col">
                <div className="staff-perm-role"><RoleBadge role={ROLES.MANAGER} /> {t('staff_mgmt.role_admin')}</div>
                <ul>
                  <li>매장안내/채팅/스탬프/쿠폰 제어</li>
                  <li>와이파이/알림/리포트/설정 조회</li>
                  <li className="perm-hidden">직원관리/결제/사업자정보 접근 불가</li>
                </ul>
              </div>
              <div className="staff-perm-col">
                <div className="staff-perm-role"><RoleBadge role={ROLES.STAFF} /> {t('staff_mgmt.role_staff')}</div>
                <ul>
                  <li>매장안내/채팅/스탬프/쿠폰 제어</li>
                  <li>와이파이/알림/리포트/설정 조회</li>
                  <li className="perm-hidden">직원관리/결제/사업자정보 접근 불가</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 법적 안내 compliance 카드 */}
          <div className="staff-compliance-card">
            <div className="staff-compliance-header">
              <ShieldAlert size={16} aria-hidden="true" />
              <h3 className="staff-compliance-title">{t('staff_mgmt.compliance_title')}</h3>
            </div>
            <ul className="staff-compliance-list">
              <li>{t('staff_mgmt.compliance_1')}</li>
              <li>{t('staff_mgmt.compliance_2')}</li>
              <li>{t('staff_mgmt.compliance_3')}</li>
            </ul>
          </div>
        </div>
      )}

      {/* 초대 모달 */}
      {showInvite && (
        <InviteModal
          onClose={() => setShowInvite(false)}
          onInvite={handleInvite}
        />
      )}

      {/* 직원 액션 모달 */}
      {selectedMember && (
        <StaffActionModal
          member={selectedMember}
          onClose={() => setSelectedMember(null)}
          onRoleChange={handleRoleChange}
          onDisable={handleDisable}
          onRemove={handleRemove}
          onResend={handleResend}
        />
      )}

      {/* 확인 모달 */}
      {confirmModal && (
        <ConfirmModal
          title={confirmModal.title}
          message={confirmModal.message}
          confirmText="확인"
          cancelText="취소"
          onConfirm={confirmModal.onConfirm}
          onCancel={() => setConfirmModal(null)}
        />
      )}
      {confirmModalEl}
    </div>
  );
};

export default StaffManagement;
