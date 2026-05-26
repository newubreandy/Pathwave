import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { Plus, X, ChevronLeft, Upload, Bell, Check, CheckCheck, Star, Info } from 'lucide-react';
import PushService from '../services/push/PushService';
import NotificationService from '../services/notification/NotificationService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import CardAvatar from '../components/common/CardAvatar';
import GroupCard, { GroupCardItem } from '../components/common/GroupCard';
import SectionTabs from '../components/common/SectionTabs';
import { NOTIFICATION_CATEGORIES } from '../services/notification/mockInbox';
import './Notifications.css';

const Notifications = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const view = searchParams.get('view') || 'list';
  
  const setView = (newView) => {
    if (newView === 'list') {
      searchParams.delete('view');
      setSearchParams(searchParams);
    } else {
      searchParams.set('view', newView);
      setSearchParams(searchParams);
    }
  };

  const [showPremiumModal, setShowPremiumModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [showQuantityModal, setShowQuantityModal] = useState(false);
  const [alertMsg, setAlertMsg] = useState('');
  const [isReadOnly, setIsReadOnly] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const fileInputRef = useRef(null);

  const showAlert = (msg) => {
    setAlertMsg(msg);
    setShowAlertModal(true);
  };

  useEffect(() => {
    // 푸시 권한 초기 요청 — 브라우저 Notification API 사용 (PushService 는 토큰 등록만 담당).
    if (typeof window !== 'undefined' && 'Notification' in window) {
      if (Notification.permission === 'default') {
        Notification.requestPermission().catch(() => {/* user denied or unavailable */});
      }
    }
  }, [view]);

  // P11 — 백엔드 quota 연동.
  // 마운트 시: 1) 내 매장 id 1회 fetch (1계정1매장) → 2) quota 통계 fetch.
  // 백엔드 응답이 없으면 0 으로 표시 (결제 안 된 신규 매장 + 안전한 디폴트).
  const [facilityId, setFacilityId] = useState(null);
  const [stats, setStats] = useState({ available: 0, used: 0, expiry: '-' });

  const loadQuota = async (fid) => {
    try {
      const res = await NotificationService.loadQuota(fid);
      const q = res?.quota || {};
      setStats((prev) => ({
        ...prev,
        available: q.available || 0,
        used:      q.used || 0,
        // expiry 는 quota_summary 미반환 — 별도 endpoint 추가 전까지 '-' 표시.
      }));
    } catch (_) {
      /* graceful: 결제 안 된 매장이면 0 유지 */
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const fid = await NotificationService.loadMyFacilityId();
        if (!fid) return;
        setFacilityId(fid);
        await loadQuota(fid);
      } catch (_) { /* 비로그인/네트워크 오류 graceful */ }
    })();
  }, []);

  // P5 (2026-05-26): mock '호텔H' 제거 — 매장명 일반화. 실 데이터는
  // GET /api/notifications (매장별) 에서 fetch — Phase 2+ 실연동.
  const [notifications, setNotifications] = useState([
    { id: 1, type: "공지", title: "샘플 공지 — 시설 점검 안내", date: "2026.05.17 18:00", status: "sent", message: "안녕하세요.\n\n시설 점검으로 운영이 일시 중단됩니다. 자세한 일정은 공지를 참고해 주세요.\n\n감사합니다.", pushLocal: true, pushGlobal: false },
    { id: 2, type: "이벤트", title: "샘플 이벤트 — 전품목 10% 할인", date: "2026.08.01 09:00", status: "pending", message: "이벤트 내용을 작성해 주세요.", pushLocal: true, pushGlobal: false }
  ]);

  const [notifKind, setNotifKind] = useState('general'); // 'general' | 'marketing'

  const [formData, setFormData] = useState({
    id: null,
    division: '',
    title: '',
    date: '',
    image: null,
    message: '',
    pushLocal: true,
    pushGlobal: false
  });

  const handleNotificationClick = (noti) => {
    // 폼 데이터 채우기
    setFormData({
      id: noti.id,
      division: noti.type,
      title: noti.title,
      date: noti.date.replace('.', '-').replace('.', '-').replace(' ', 'T'), // datetime-local format
      image: null,
      message: noti.message || '',
      pushLocal: noti.pushLocal !== undefined ? noti.pushLocal : true,
      pushGlobal: noti.pushGlobal || false
    });

    if (noti.status === 'sent') {
      // 발송 완료된 항목은 무조건 읽기 전용 및 잠금
      setIsReadOnly(true);
      setIsLocked(true);
      setView('form');
    } else {
      // 발송 대기 중인 항목
      setIsReadOnly(true); // 우선 읽기 전용(View Mode)으로 열림
      
      const now = new Date();
      const targetDate = new Date(noti.date.replace(/\./g, '/')); 
      const hoursDiff = (targetDate - now) / (1000 * 60 * 60);

      if (hoursDiff < 12) {
        setIsLocked(true); // 12시간 락
      } else {
        setIsLocked(false);
      }
      setView('form');
    }
  };

  const handleNewNotificationClick = () => {
    setShowQuantityModal(true);
  };

  const handleContinueWriting = () => {
    setShowQuantityModal(false);
    handleNewNotification();
  };

  const handleNewNotification = () => {
    setFormData({
      id: null, division: '', title: '', date: '', image: null, message: '', pushLocal: false, pushGlobal: false
    });
    setNotifKind('general');
    setIsReadOnly(false);
    setIsLocked(false);
    setView('form');
  };

  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData({ ...formData, image: { file, name: file.name, preview: reader.result } });
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setFormData({ ...formData, image: null });
  };

  const handlePushToggle = (type, isChecked) => {
    if (isChecked && stats.available <= 0) {
      setShowPremiumModal(true);
      return;
    }
    setFormData({ ...formData, [type]: isChecked });
  };

  const confirmPremium = () => {
    setShowPremiumModal(false);
    alert('서비스 신청 페이지로 이동합니다.');
  };

  const handleSave = () => {
    if (!formData.division) {
      showAlert(t('noti.msg_require_division'));
      return;
    }
    if (!formData.title.trim() || formData.title.trim().length < 2) {
      showAlert(t('noti.msg_require_title_length'));
      return;
    }
    if (!formData.date) {
      showAlert(t('noti.msg_require_date'));
      return;
    }
    if (!formData.message.trim() || formData.message.trim().length < 20) {
      showAlert(t('noti.msg_require_message_length'));
      return;
    }

    const selectedDate = new Date(formData.date);
    const now = new Date();
    const hoursDiff = (selectedDate - now) / (1000 * 60 * 60);
    
    if (hoursDiff < 12) {
      const minDate = new Date(now.getTime() + 12 * 60 * 60 * 1000);
      const minDateString = `${minDate.getFullYear()}-${String(minDate.getMonth() + 1).padStart(2, '0')}-${String(minDate.getDate()).padStart(2, '0')} ${String(minDate.getHours()).padStart(2, '0')}:${String(minDate.getMinutes()).padStart(2, '0')}`;
      showAlert(t('noti.msg_date_past', { minDate: minDateString }));
      return;
    }

    // P11 — expiry 검증은 백엔드 quota.expires_at 이 명확한 경우만.
    // stats.expiry 가 '-' (백엔드 미반환) 이면 클라이언트 검증 skip → 백엔드에서 quota 검증으로 잡힘.
    if (stats.expiry && stats.expiry !== '-') {
      const expiryDate = new Date(stats.expiry.replace(/\./g, '/'));
      if (!Number.isNaN(expiryDate.getTime())) {
        expiryDate.setHours(23, 59, 59, 999);
        if (selectedDate > expiryDate) {
          showAlert(t('noti.msg_date_expiry', { expiry: stats.expiry }));
          return;
        }
      }
    }

    if (!formData.pushLocal && !formData.pushGlobal) {
      showAlert(t('noti.msg_require_push'));
      return;
    }
    
    setShowConfirmModal(true);
  };

  const confirmSave = async () => {
    setShowConfirmModal(false);

    // 정보통신망법 준수: 마케팅 알림이면 본문 앞 [광고] prefix + 수신거부 footer 자동 추가
    let finalTitle = formData.title;
    let finalBody = formData.message;
    if (notifKind === 'marketing') {
      finalTitle = `[광고] ${formData.title}`;
      finalBody = `${formData.message}\n\n수신 거부: 설정 > 알림 동의`;
    }

    // P11 — 백엔드 알림 신청 (12h/quota/AI 검토는 서버에서). pushGlobal/pushLocal
    // 은 v1 에선 전부 'all_visited'(매장 방문 이력 있는 사용자) 로 매핑한다.
    if (!facilityId) {
      showAlert('매장 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.');
      return;
    }
    try {
      // datetime-local → ISO 8601
      const scheduledAt = new Date(formData.date).toISOString();
      const res = await NotificationService.createNotification(facilityId, {
        title:        finalTitle,
        body:         finalBody,
        target_type:  'all_visited',
        scheduled_at: scheduledAt,
      });
      // 백엔드가 정책 응답 메시지를 같이 줌 — UX 일관성 위해 그대로 노출.
      const backendMsg = res?.message;
      const status     = res?.notification?.status;
      // quota 다시 로드 (방금 차감되진 않지만, 신규 매장 첫 결제 직후 등 갱신 케이스)
      await loadQuota(facilityId);

      if (status === 'unpaid') {
        // 결제 부족 → 결제 유도 모달
        showAlert(backendMsg || '발송 수량이 부족합니다. 결제 후 활성화됩니다.');
        return;
      }
      if (status === 'review') {
        showAlert(backendMsg || '운영팀 검토 후 발송됩니다.');
        setShowSuccessModal(true);
        return;
      }
      // pending — 정상 예약
      setShowSuccessModal(true);
    } catch (err) {
      showAlert(err?.message || '알림 신청에 실패했습니다.');
    }
  };

  const closeSuccess = () => {
    setShowSuccessModal(false);
    setView('list');
    setFormData({
      division: '', title: '', date: '', image: null, message: '', pushLocal: true, pushGlobal: false
    });
  };

  if (view === 'form') {
    return (
      <div className="common-form-page">
        <header className="common-form-header">
          <button className="back-btn" aria-label="뒤로 가기" onClick={() => setView('list')}>
            <ChevronLeft size={24} />
          </button>
          <h1>
            {isReadOnly ? t('noti.title_view') : (formData.id ? t('noti.title_edit') : t('noti.title_add'))}
          </h1>
        </header>

        <div style={{ marginBottom: '1rem' }}>
          <p className="sub-title" style={{ marginBottom: '2rem', whiteSpace: 'pre-line', textAlign: 'center' }}>
            {isReadOnly ? t('noti.desc_readonly') : t('noti.desc_form')}
          </p>

          {/* 알림 종류 — 일반 / 마케팅 (정보통신망법 구분) */}
          <div className="form-group">
            <div className="form-label">{t('notif.send_title')}</div>
            <div className="form-content">
              <div style={{ display: 'flex', gap: 'var(--pw-space-6)', marginTop: 'var(--pw-space-2)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--pw-space-2)', cursor: isReadOnly ? 'default' : 'pointer', color: 'var(--pw-text)', fontSize: 'var(--pw-body-size)' }}>
                  <input
                    type="radio"
                    name="notifKind"
                    value="general"
                    checked={notifKind === 'general'}
                    onChange={() => setNotifKind('general')}
                    disabled={isReadOnly}
                    style={{ accentColor: 'var(--pw-accent)', width: '18px', height: '18px' }}
                  />
                  {t('notif.send_kind_general')}
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--pw-space-2)', cursor: isReadOnly ? 'default' : 'pointer', color: 'var(--pw-text)', fontSize: 'var(--pw-body-size)' }}>
                  <input
                    type="radio"
                    name="notifKind"
                    value="marketing"
                    checked={notifKind === 'marketing'}
                    onChange={() => setNotifKind('marketing')}
                    disabled={isReadOnly}
                    style={{ accentColor: 'var(--pw-accent)', width: '18px', height: '18px' }}
                  />
                  {t('notif.send_kind_marketing')}
                </label>
              </div>
              {notifKind === 'marketing' && (
                <div style={{
                  marginTop: 'var(--pw-space-3)',
                  padding: 'var(--pw-space-3) var(--pw-space-4)',
                  background: 'rgba(245, 158, 11, 0.10)',
                  border: '1px solid rgba(245, 158, 11, 0.35)',
                  borderRadius: 'var(--pw-radius-sm)',
                  color: '#F59E0B',
                  fontSize: 'var(--pw-caption-size)',
                  lineHeight: '1.6',
                  display: 'flex',
                  gap: 'var(--pw-space-2)',
                  alignItems: 'flex-start'
                }}>
                  <Info size={14} style={{ flexShrink: 0, marginTop: '2px' }} />
                  <span>{t('notif.send_kind_warning')}</span>
                </div>
              )}
            </div>
          </div>

          {/* Division */}
          <div className="form-group">
            <div className="form-label">{t('noti.label_division')}</div>
            <div className="form-content">
              <select 
                className="form-input-line" 
                value={formData.division} 
                onChange={e => setFormData({...formData, division: e.target.value})}
                disabled={isReadOnly}
              >
                <option value="" disabled>{t('noti.ph_division')}</option>
                <option value={t('noti.opt_benefit')}>{t('noti.opt_benefit')}</option>
                <option value={t('noti.opt_notice')}>{t('noti.opt_notice')}</option>
                <option value={t('noti.opt_urgent')}>{t('noti.opt_urgent')}</option>
              </select>
              <div className="form-hint">{t('noti.hint_division')}</div>
            </div>
          </div>

          {/* Title */}
          <div className="form-group">
            <div className="form-label">{t('noti.label_title')}</div>
            <div className="form-content">
              <input 
                type="text" 
                className={`form-input-line ${isReadOnly ? 'disabled-text' : ''}`}
                placeholder={t('noti.ph_title')} 
                value={formData.title}
                onChange={e => setFormData({...formData, title: e.target.value})}
                disabled={isReadOnly}
              />
            </div>
          </div>

          {/* Date */}
          <div className="form-group">
            <div className="form-label">{t('noti.label_date')}</div>
            <div className="form-content">
              <div className="date-row">
                {formData.date && isReadOnly ? (
                  <div className="date-value disabled-text">{formData.date.replace('T', '   ')}</div>
                ) : (
                  <input 
                    type="datetime-local" 
                    className="form-input-line" 
                    style={{ border: 'none', padding: 0 }}
                    value={formData.date}
                    disabled={isReadOnly}
                    onChange={e => {
                      setFormData({...formData, date: e.target.value});
                    }}
                  />
                )}
              </div>
              <div className="form-hint">{t('noti.hint_date1')}<br/>{t('noti.hint_date2')}</div>
            </div>
          </div>

          {/* Image */}
          <div className="form-group">
            <div className="form-label">{t('noti.label_image')}</div>
            <div className="form-content">
              {!isReadOnly && !formData.image && (
                <div
                  onClick={() => fileInputRef.current.click()}
                  className="noti-image-dropzone"
                >
                  <Upload size={24} />
                  <div>{t('noti.no_image')}</div>
                </div>
              )}
              {isReadOnly && !formData.image && (
                <div style={{ color: '#94A3B8' }}>{t('noti.no_image_readonly')}</div>
              )}
              
              {formData.image && (
                <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
                  <img src={formData.image.preview} alt="preview" className="image-preview" style={{ marginTop: 0 }} />
                  {!isReadOnly && (
                    <button 
                      onClick={removeImage} 
                      style={{ position: 'absolute', top: '10px', right: '10px', background: 'rgba(0,0,0,0.5)', color: 'white', border: 'none', borderRadius: '50%', width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0 }}
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              )}
              {!isReadOnly && (
                <input type="file" ref={fileInputRef} style={{ display: 'none' }} accept="image/*" onChange={handleImageChange} />
              )}
              <div className="form-hint" style={{ marginTop: '0.5rem' }}>
                {t('noti.hint_image')}<br/>
                {t('noti.hint_image_ratio')}
              </div>
            </div>
          </div>

          {/* Message */}
          <div className="form-group">
            <div className="form-label">{t('noti.label_message')}</div>
            <div className="form-content">
              {isReadOnly ? (
                <div className="readonly-message-box">
                  {formData.message}
                </div>
              ) : (
                <div style={{ position: 'relative' }}>
                  <textarea 
                    className="form-textarea" 
                    placeholder={t('noti.ph_message')}
                    value={formData.message}
                    onChange={e => setFormData({...formData, message: e.target.value})}
                    maxLength={500}
                  />
                  <div style={{ position: 'absolute', bottom: '1rem', right: '1rem', fontSize: '0.8rem', color: '#94A3B8' }}>
                    {formData.message.length} / 500
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Push Options */}
          <div className="form-group">
            <div className="form-label">{t('noti.label_push')}</div>
            <div className="form-content">
              
              {/* 공통 .toggle-switch (Settings 와 동일 구조) — inline style 제거, 공통 톤 사용 */}
              <div style={{ marginBottom: '1rem' }}>
                <div className="toggle-row" style={{ marginBottom: 0 }}>
                  <label className="toggle-switch">
                    <input type="checkbox" checked={formData.pushLocal} onChange={e => handlePushToggle('pushLocal', e.target.checked)} disabled={isReadOnly} />
                    <span className="toggle-track" />
                    <span className="toggle-thumb" />
                    <span className="toggle-text">{formData.pushLocal ? 'ON' : 'OFF'}</span>
                  </label>
                  <span className="toggle-label">{t('noti.label_push_local')}</span>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <div className="toggle-row" style={{ marginBottom: 0 }}>
                  <label className="toggle-switch">
                    <input type="checkbox" checked={formData.pushGlobal} onChange={e => handlePushToggle('pushGlobal', e.target.checked)} disabled={isReadOnly} />
                    <span className="toggle-track" />
                    <span className="toggle-thumb" />
                    <span className="toggle-text">{formData.pushGlobal ? 'ON' : 'OFF'}</span>
                  </label>
                  <span className="toggle-label">{t('noti.label_push_global')}</span>
                </div>
              </div>
              
              <div className="form-hint">{t('noti.hint_push')}</div>

            </div>
          </div>

        </div>

        {/* Sticky Actions */}
        <BottomActionBar>
          {isReadOnly ? (
            <>
              <Button variant="outline" fullWidth onClick={() => setView('list')}>{t('noti.btn_close')}</Button>
              {formData.id && !isLocked && (
                <Button variant="primary" fullWidth onClick={() => setIsReadOnly(false)}>{t('noti.btn_edit')}</Button>
              )}
            </>
          ) : (
            <>
              <Button variant="outline" fullWidth onClick={() => {
                if (formData.id) {
                  setIsReadOnly(true);
                } else {
                  setView('list');
                }
              }}>{t('noti.btn_cancel')}</Button>
              <Button variant="primary" fullWidth onClick={handleSave}>{t('noti.btn_save')}</Button>
            </>
          )}
        </BottomActionBar>

        {/* Modals */}


        {showAlertModal && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="modal-body" style={{ whiteSpace: 'pre-line', paddingTop: '1rem', paddingBottom: '1rem' }}>
                {alertMsg}
              </div>
              <div className="modal-actions">
                <button className="modal-btn confirm" onClick={() => setShowAlertModal(false)}>{t('noti.btn_confirm')}</button>
              </div>
            </div>
          </div>
        )}

        {showConfirmModal && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h2 style={{ fontSize: '1.2rem', margin: '2rem 0 0.5rem', color: '#1E293B' }}>{t('noti.title_confirm_save')}</h2>
              <div className="modal-body" style={{ paddingTop: '1rem', whiteSpace: 'pre-line' }}>
                {t('noti.msg_confirm_save')}
              </div>
              <div className="modal-actions">
                <button className="modal-btn cancel" onClick={() => setShowConfirmModal(false)}>{t('noti.btn_cancel')}</button>
                <button className="modal-btn confirm" onClick={confirmSave}>{t('noti.btn_save')}</button>
              </div>
            </div>
          </div>
        )}

        {showPremiumModal && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="modal-body" style={{ whiteSpace: 'pre-line' }}>
                {t('noti.premium_alert')}
              </div>
              <div className="modal-actions">
                <button className="modal-btn cancel" onClick={() => setShowPremiumModal(false)}>{t('noti.btn_cancel')}</button>
                <button className="modal-btn confirm" onClick={confirmPremium}>{t('noti.btn_apply')}</button>
              </div>
            </div>
          </div>
        )}

        {showSuccessModal && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="modal-body">
                {t('noti.save_success')}
              </div>
              <div className="modal-actions">
                <button className="modal-btn confirm" style={{ borderLeft: 'none' }} onClick={closeSuccess}>{t('noti.btn_confirm')}</button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // List View — 탭 구조 (사용자 요구 2026-05-10):
  //   inbox  : 알림리스트 (받은 알림 — Notification Center)
  //   send   : 알림발송관리 (기존 발송 캠페인 관리)
  const tab = searchParams.get('tab') || 'inbox';
  const setTab = (newTab) => {
    if (newTab === 'inbox') searchParams.delete('tab');
    else searchParams.set('tab', newTab);
    setSearchParams(searchParams);
  };

  return (
    <div className="notifications-page">
      <div className="page-header-section">
        <h1 className="page-title">알림</h1>
        <p className="sub-title">받은 알림 확인과 알림 발송을 관리하세요.</p>
      </div>

      {/* 탭 — 공통 SectionTabs (사용자 요구 2026-05-10: 와이파이/리포트와 동일 톤) */}
      <SectionTabs
        tabs={[
          // P10 (2026-05-26): MOCK_INBOX count 제거 — 실시간 count 는 NotificationInbox 내부에서 처리.
          { key: 'inbox', label: '알림리스트' },
          { key: 'send',  label: '알림발송관리' },
        ]}
        value={tab}
        onChange={setTab}
        ariaLabel="알림 카테고리"
      />

      {/* ── 알림리스트 (Inbox) — 받은 알림 ── */}
      {tab === 'inbox' && <NotificationInbox />}

      {/* ── 알림발송관리 — 기존 view ── */}
      {tab === 'send' && (<>


      {/* Stats Dashboard */}
      <div className="usage-stats-card">
        <div className="stat-item">
          <span className="stat-label">{t('noti.stats_available')}</span>
          <span className="stat-value highlight">{stats.available.toLocaleString()}건</span>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <span className="stat-label">{t('noti.stats_used')}</span>
          <span className="stat-value">{stats.used.toLocaleString()}건</span>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <span className="stat-label">{t('noti.stats_expiry')}</span>
          <span className="stat-value">{stats.expiry}</span>
        </div>
      </div>



      {/* List */}
      <div className="notification-list">
        {[...notifications].sort((a, b) => new Date(b.date.replace(/\./g, '/')) - new Date(a.date.replace(/\./g, '/'))).map(noti => {
          const now = new Date();
          const targetDate = new Date(noti.date.replace(/\./g, '/'));
          const isLocked = noti.status === 'pending' && ((targetDate - now) / (1000 * 60 * 60)) < 12;
          const statusClass = noti.status === 'sent' ? 'sent' : (isLocked ? 'pending-locked' : 'pending');
          const badgeClass = noti.type === '이벤트' ? 'badge-event' : (noti.type === '혜택' ? 'badge-benefit' : 'badge-notice');

          return (
          <div className="noti-card" key={noti.id} onClick={() => handleNotificationClick(noti)}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--pw-space-4)' }}>
              <div className={`noti-icon ${noti.status === 'sent' ? 'sent' : 'active'}`}>
                <Bell size={24} />
              </div>
              <div className="noti-info">
                <div className="noti-meta">
                  <span className={`noti-badge ${badgeClass}`}>{noti.type}</span>
                  <span className="noti-date">{noti.date} 발송</span>
                </div>
                <span className="noti-title">{noti.title}</span>
              </div>
            </div>
            <div className={`noti-status ${statusClass}`}>
              {noti.status === 'sent' ? t('noti.status_sent') : t('noti.status_pending')}
            </div>
          </div>
        )})}
        {notifications.length === 0 && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#94A3B8', border: '1px dashed #E2E8F0', borderRadius: '12px' }}>
            {t('noti.empty_list')}
          </div>
        )}
      </div>

      {showQuantityModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2 style={{ fontSize: '1.2rem', margin: '2rem 0 0.5rem', color: '#1E293B' }}>알림 발송 수량 안내</h2>
            <div className="modal-body" style={{ paddingTop: '1rem', whiteSpace: 'pre-line', textAlign: 'center' }}>
              {stats.available < 100 ? (
                <p style={{ marginBottom: '1rem', lineHeight: '1.6' }}>
                  현재 잔여 발송 수량이 100개 미만입니다.<br />
                  대량 발송 시 서비스가 제한될 수 있습니다.
                </p>
              ) : (
                <p style={{ marginBottom: '1rem', lineHeight: '1.6' }}>
                  현재 발송 가능한 알림은 <strong style={{ color: 'var(--pw-accent)' }}>{stats.available.toLocaleString()}</strong>개 입니다.
                </p>
              )}
            </div>
            <div className="modal-actions">
              <button className="modal-btn cancel" onClick={() => setShowQuantityModal(false)}>닫기</button>
              {stats.available < 100 ? (
                <button className="modal-btn confirm" style={{ background: '#F1F5F9', color: '#1E293B' }} onClick={() => { setShowQuantityModal(false); setShowPremiumModal(true); }}>구매하기</button>
              ) : (
                <button className="modal-btn confirm" onClick={handleContinueWriting}>작성</button>
              )}
            </div>
          </div>
        </div>
      )}

      {showAlertModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-body" style={{ whiteSpace: 'pre-line', paddingTop: '1rem', paddingBottom: '1rem' }}>
              {alertMsg}
            </div>
            <div className="modal-actions">
              <button className="modal-btn confirm" onClick={() => setShowAlertModal(false)}>{t('noti.btn_confirm')}</button>
            </div>
          </div>
        </div>
      )}

      {showPremiumModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-body" style={{ whiteSpace: 'pre-line' }}>
              {t('noti.premium_alert')}
            </div>
            <div className="modal-actions">
              <button className="modal-btn cancel" onClick={() => setShowPremiumModal(false)}>{t('noti.btn_cancel')}</button>
              <button className="modal-btn confirm" onClick={confirmPremium}>{t('noti.btn_apply')}</button>
            </div>
          </div>
        </div>
      )}

      <BottomActionBar>
        <Button variant="primary" fullWidth icon={<Plus size={18} />} onClick={handleNewNotificationClick}>
          {t('noti.btn_add')}
        </Button>
      </BottomActionBar>
      </>)}
    </div>
  );
};

/* ══════════════════════════════════════════════
   NotificationInbox — 받은 알림 (Notification Center)
   날짜 그룹핑 + 카테고리별 아이콘 + 읽음 처리 + important 상단 고정.
   ══════════════════════════════════════════════ */
function NotificationInbox() {
  // P10 (2026-05-26): MOCK_INBOX 제거 — 백엔드 listNotifications(fid) 실연동.
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const fid = await NotificationService.loadMyFacilityId();
        if (!fid) {
          if (alive) { setItems([]); setLoading(false); }
          return;
        }
        const res = await NotificationService.listNotifications(fid);
        const list = res?.notifications || res?.data || res || [];
        if (alive) setItems(Array.isArray(list) ? list : []);
      } catch (err) {
        console.error('NotificationInbox load failed', err);
        if (alive) setItems([]);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const unreadCount = items.filter((n) => !n.read_at).length;

  const markAsRead = (id) => {
    setItems((prev) => prev.map((n) => n.id === id ? { ...n, read_at: new Date().toISOString() } : n));
  };
  const markAllAsRead = () => {
    setItems((prev) => prev.map((n) => n.read_at ? n : { ...n, read_at: new Date().toISOString() }));
  };

  // 날짜 그룹핑 — 오늘 / 어제 / 이전
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86_400_000).toDateString();
  const groupOf = (iso) => {
    const d = new Date(iso).toDateString();
    if (d === today) return '오늘';
    if (d === yesterday) return '어제';
    return '이전';
  };

  // 정렬: important 우선 → 미확인 우선 → 최신순
  const sorted = [...items].sort((a, b) => {
    if (a.important !== b.important) return b.important - a.important;
    if (!a.read_at && b.read_at) return -1;
    if (a.read_at && !b.read_at) return 1;
    return new Date(b.created_at) - new Date(a.created_at);
  });

  // 그룹핑
  const groups = sorted.reduce((acc, n) => {
    const g = groupOf(n.created_at);
    (acc[g] = acc[g] || []).push(n);
    return acc;
  }, {});

  const formatTime = (iso) => {
    const d = new Date(iso);
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return '방금 전';
    if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
    return `${d.getMonth() + 1}월 ${d.getDate()}일`;
  };

  return (
    <div className="noti-inbox">
      {/* 상단 요약 + 전체 읽음 */}
      <div className="noti-inbox-header">
        <div className="noti-inbox-summary">
          전체 {items.length}건 · <strong>읽지 않음 {unreadCount}건</strong>
        </div>
        {unreadCount > 0 && (
          <button className="noti-inbox-readall" onClick={markAllAsRead}>
            <CheckCheck size={14} /> 전체 읽음 처리
          </button>
        )}
      </div>

      {/* 빈 상태 */}
      {items.length === 0 && (
        <div className="noti-inbox-empty">받은 알림이 없습니다.</div>
      )}

      {/* 날짜 그룹별 GroupCard */}
      {['오늘', '어제', '이전'].map((groupName) => {
        const list = groups[groupName];
        if (!list?.length) return null;
        return (
          <GroupCard
            key={groupName}
            variant="container"
            title={groupName}
            subtitle={`${list.length}건`}
            collapsible={groupName !== '오늘'}
          >
            {list.map((n) => {
              const meta = NOTIFICATION_CATEGORIES[n.category] || { icon: Bell, variant: 'neutral', label: n.category };
              const Icon = meta.icon;
              const isUnread = !n.read_at;
              return (
                <GroupCardItem
                  key={n.id}
                  onClick={() => isUnread && markAsRead(n.id)}
                  className={`noti-inbox-item ${isUnread ? 'is-unread' : ''} ${n.important ? 'is-important' : ''}`}
                >
                  <CardAvatar variant={meta.variant} size="md">
                    <Icon strokeWidth={2} />
                  </CardAvatar>
                  <div className="noti-inbox-body">
                    <div className="noti-inbox-head">
                      <span className="noti-inbox-cat">{meta.label}</span>
                      {n.important && <Star size={12} className="noti-inbox-star" />}
                      <span className="noti-inbox-time">{formatTime(n.created_at)}</span>
                    </div>
                    <p className="noti-inbox-title">{n.title}</p>
                    <p className="noti-inbox-text">{n.body}</p>
                  </div>
                  {isUnread && <span className="noti-inbox-dot" aria-label="미확인" />}
                </GroupCardItem>
              );
            })}
          </GroupCard>
        );
      })}
    </div>
  );
}

export default Notifications;
