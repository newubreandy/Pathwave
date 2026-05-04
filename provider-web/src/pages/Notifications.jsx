import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { Plus, X, ChevronLeft, Upload, Bell } from 'lucide-react';
import PushService from '../services/push/PushService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
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
    // 푸시 권한 초기 요청 (PushService 연동)
    PushService.requestPermission();
  }, [view]);

  // Mock Data
  const stats = {
    available: 0, // 테스트를 위해 0으로 고정
    used: 245,
    expiry: "2026.12.31"
  };

  const [notifications, setNotifications] = useState([
    { id: 1, type: "공지", title: "지하 2층 사우나 청소안내", date: "2022.05.17 18:00", status: "sent", message: "안녕하세요 호텔H입니다.\n\n2022.05.17 18:00 ~ 24:00 남성 및 여성 사우나 내부청소로 운영이 중단되오니 이점 참고하시어 이용에 불편이 없도록 이용하셨으면 좋겠습니다.\n\n감사합니다.", pushLocal: true, pushGlobal: false },
    { id: 2, type: "이벤트", title: "여름맞이 전품목 10% 할인", date: "2026.08.01 09:00", status: "pending", message: "이벤트 내용입니다.", pushLocal: true, pushGlobal: false }
  ]);

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

    const expiryDate = new Date(stats.expiry.replace(/\./g, '/'));
    expiryDate.setHours(23, 59, 59, 999);
    if (selectedDate > expiryDate) {
      showAlert(t('noti.msg_date_expiry', { expiry: stats.expiry }));
      return;
    }

    if (!formData.pushLocal && !formData.pushGlobal) {
      showAlert(t('noti.msg_require_push'));
      return;
    }
    
    setShowConfirmModal(true);
  };

  const confirmSave = async () => {
    setShowConfirmModal(false);
    
    // 1차 백엔드 모듈 연동: 푸시 알림 발송 (Mock)
    if (formData.pushGlobal) {
      await PushService.sendBulkNotification(['user1', 'user2', 'user3'], {
        title: formData.title,
        body: formData.message
      });
    } else if (formData.pushLocal) {
      await PushService.sendNotification('local_user', {
        title: formData.title,
        body: formData.message
      });
    }

    setShowSuccessModal(true);
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
          <button className="back-btn" onClick={() => setView('list')}>
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
                  style={{ border: '1px dashed var(--border)', borderRadius: '8px', padding: '2rem', textAlign: 'center', cursor: 'pointer', color: '#94A3B8', background: '#F8FAFC' }}
                >
                  <Upload size={24} style={{ marginBottom: '0.5rem' }} />
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
              
              <div style={{ marginBottom: '1rem' }}>
                <div className="toggle-row" style={{ marginBottom: 0 }}>
                  <label className="toggle-switch">
                    <input type="checkbox" checked={formData.pushLocal} onChange={e => handlePushToggle('pushLocal', e.target.checked)} disabled={isReadOnly} />
                    <span className="toggle-slider" style={{ backgroundColor: formData.pushLocal ? 'var(--primary)' : '#64748B', opacity: isReadOnly ? 0.6 : 1 }}><span className="toggle-text">{formData.pushLocal ? 'ON' : 'OFF'}</span></span>
                  </label>
                  <span className="toggle-label">{t('noti.label_push_local')}</span>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <div className="toggle-row" style={{ marginBottom: 0 }}>
                  <label className="toggle-switch">
                    <input type="checkbox" checked={formData.pushGlobal} onChange={e => handlePushToggle('pushGlobal', e.target.checked)} disabled={isReadOnly} />
                    <span className="toggle-slider" style={{ backgroundColor: formData.pushGlobal ? 'var(--primary)' : '#64748B', opacity: isReadOnly ? 0.6 : 1 }}>
                      <span className="toggle-text">{formData.pushGlobal ? 'ON' : 'OFF'}</span>
                    </span>
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

  // List View
  return (
    <div className="notifications-page">
      <div className="page-header-section">
        <h1 className="page-title">{t('noti.title_list', '알림 발송')}</h1>
        <p className="sub-title">알림 발송 현황 및 내역을 관리하세요.</p>
      </div>

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
                  현재 발송 가능한 알림은 <strong style={{ color: 'var(--primary)' }}>{stats.available.toLocaleString()}</strong>개 입니다.
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
    </div>
  );
};

export default Notifications;
