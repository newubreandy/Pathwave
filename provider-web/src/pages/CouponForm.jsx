import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChevronLeft, Search, Plus, Minus, X, Camera } from 'lucide-react';
import BottomActionBar from '../components/common/BottomActionBar';
import Button from '../components/common/Button';
import ConfirmModal from '../components/common/ConfirmModal';
import './CouponForm.css';

const CouponForm = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { action, id } = useParams(); // 'add', 'edit', 'view'
  
  const isViewMode = action === 'view';
  const isEditMode = action === 'edit' || id;

  const [formData, setFormData] = useState({
    title: '',
    exposureStart: '',
    exposureEnd: '',
    progressStart: '',
    progressEnd: '',
    images: [],
    message: '',
    presentsTitle: '',
    presentsCount: 0,
    isUnlimited: false,
    isDirectInput: false,
    location: '',
    pushVisitors: false,
    pushAll: false
  });

  const availableCoupons = 5;
  const pushAvailable = 50;

  const [modalState, setModalState] = useState({
    isOpen: false,
    message: ''
  });

  const [showLimitModal, setShowLimitModal] = useState(false);
  const [limitMsg, setLimitMsg] = useState('');

  useEffect(() => {
    // Scroll to top on mount
    window.scrollTo(0, 0);

    if (isEditMode) {
      // Load dummy data for edit mode based on screenshot
      setFormData({
        title: '호텔H 썬베드 선착순 50명 무료 이용권 증정이벤트',
        exposureStart: '2022-05-01',
        exposureEnd: '2022-05-31',
        progressStart: '2022-05-01',
        progressEnd: '2022-05-31',
        images: ['https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?w=400'],
        message: '호텔H 수영장 이용권 알림을 보여주시는 고객(선착순 방문 20명 대상)께 입장 시, 썬베드 1개를 무료로 빌려 드립니다.\n대여시간은 1시간이며, 추가 이용시 추가 비용이 발생할 수 있습니다.\n해당 이벤트는 선착순으로 진행되며, 20명이 넘을시 별도의 알림없이 자동으로 종료 됩니다.',
        presentsTitle: '썬베드 무료이용권',
        presentsCount: 50,
        isUnlimited: false,
        isDirectInput: false,
        location: '수영장 입구',
        pushVisitors: true,
        pushAll: true
      });
    }
  }, [isEditMode, action]);

  const handleBenefitValidation = (actionFn) => {
    if (availableCoupons < 10) {
      setLimitMsg('보유쿠폰은 최소 10장 이상이어야 합니다.\n구매하시겠습니까?');
      setShowLimitModal(true);
      return;
    }
    actionFn();
  };

  const handlePushToggle = (field) => {
    if (!formData[field] && pushAvailable < 100) {
      setLimitMsg('현재 잔여 발송 수량이 100개 미만입니다.\n대량 발송 시 서비스가 제한될 수 있습니다.\n구매하시겠습니까?');
      setShowLimitModal(true);
      return;
    }
    setFormData({...formData, [field]: !formData[field]});
  };

  const handleSave = () => {
    setModalState({
      isOpen: true,
      message: t('coupon.msg_saved', '이벤트가 수정되었습니다.')
    });
  };

  const closeModalAndGoBack = () => {
    setModalState({ isOpen: false, message: '' });
    navigate('/dashboard/coupons');
  };

  return (
    <div className="common-form-page">
      <div className="common-form-header">
        <button className="back-btn" onClick={() => navigate('/dashboard/coupons')}>
          <ChevronLeft size={24} />
        </button>
        <h1>{isViewMode ? t('coupon.title_view') : t('coupon.title_edit')}</h1>
      </div>

      <div className="coupon-desc-text">
        <p>{t('coupon.desc').split('\n')[0]}</p>
        <p style={{ marginTop: '0.5rem' }}>{t('coupon.desc').split('\n')[1]}</p>
      </div>

      <div className="coupon-form-container">
        
        {/* Title */}
        <div className="form-group">
          <div className="form-label">{t('coupon.label_title')}</div>
          <div className="form-content">
            <input 
              type="text" 
              className="form-input-line" 
              placeholder={t('coupon.ph_title')}
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              disabled={isViewMode}
            />
          </div>
        </div>

        {/* Date: Exposure */}
        <div className="form-group">
          <div className="form-label">{t('coupon.date_exposure')}</div>
          <div className="form-content">
            {isViewMode ? (
               <div className="date-value">{formData.exposureStart} ~ {formData.exposureEnd}</div>
            ) : (
              <div className="date-range-group">
                <input type="date" className="date-input" value={formData.exposureStart} onChange={(e) => setFormData({...formData, exposureStart: e.target.value})} />
                <span className="date-separator">~</span>
                <input type="date" className="date-input" value={formData.exposureEnd} onChange={(e) => setFormData({...formData, exposureEnd: e.target.value})} />
              </div>
            )}
            <div className="form-hint">{t('coupon.hint_date_exposure')}</div>
          </div>
        </div>

        {/* Date: Progress */}
        <div className="form-group">
          <div className="form-label">{t('coupon.date_progress')}</div>
          <div className="form-content">
            {isViewMode ? (
               <div className="date-value">{formData.progressStart} ~ {formData.progressEnd}</div>
            ) : (
              <div className="date-range-group">
                <input type="date" className="date-input" value={formData.progressStart} onChange={(e) => setFormData({...formData, progressStart: e.target.value})} />
                <span className="date-separator">~</span>
                <input type="date" className="date-input" value={formData.progressEnd} onChange={(e) => setFormData({...formData, progressEnd: e.target.value})} />
              </div>
            )}
            <div className="form-hint">{t('coupon.hint_date_progress')}</div>
          </div>
        </div>

        {/* Image */}
        <div className="form-group">
          <div className="form-label">{t('coupon.label_image')}</div>
          <div className="form-content">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {formData.images.map((img, idx) => (
                <div key={idx} style={{ position: 'relative', width: '100%' }}>
                  <img src={img} alt={`Coupon ${idx}`} style={{ width: '100%', maxHeight: '500px', borderRadius: '8px', objectFit: 'cover' }} />
                  {!isViewMode && (
                    <button 
                      onClick={() => {
                         const newImages = [...formData.images];
                         newImages.splice(idx, 1);
                         setFormData({...formData, images: newImages});
                      }} 
                      style={{ position: 'absolute', top: '-10px', right: '-10px', background: 'var(--danger)', color: 'white', borderRadius: '50%', width: '24px', height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: 'none', cursor: 'pointer', zIndex: 10 }}
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
              ))}
              {!isViewMode && formData.images.length < 3 && (
                <div 
                  style={{ width: '100%', height: '150px', border: '2px dashed var(--border)', borderRadius: '8px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-hint)' }}
                  onClick={() => {
                    const newImages = [...formData.images, 'https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?w=400'];
                    setFormData({...formData, images: newImages});
                  }}
                >
                  <Camera size={32} style={{ marginBottom: '0.5rem' }} />
                  <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{t('coupon.btn_select_image')} ({formData.images.length}/3)</span>
                </div>
              )}
            </div>
            <div className="form-hint" style={{ marginTop: '0.5rem' }}>{t('coupon.hint_image')}</div>
          </div>
        </div>

        {/* Message */}
        <div className="form-group">
          <div className="form-label">{t('coupon.label_message')}</div>
          <div className="form-content">
            {isViewMode ? (
              <div className="coupon-message-box" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
                {formData.message}
              </div>
            ) : (
              <textarea 
                className="form-input-line" 
                style={{ width: '100%', minHeight: '150px', padding: '1rem', border: '1px solid var(--border)', borderRadius: '8px', resize: 'vertical', lineHeight: '1.6', color: 'var(--text-primary)' }}
                placeholder={t('coupon.ph_message')}
                value={formData.message}
                onChange={(e) => setFormData({...formData, message: e.target.value})}
              />
            )}
          </div>
        </div>

        {/* Presents */}
        <div className="form-group">
          <div className="form-label">{t('coupon.label_presents')}</div>
          <div className="form-content">
            <input 
              type="text" 
              className="form-input-line" 
              placeholder={t('coupon.ph_presents')}
              value={formData.presentsTitle}
              onChange={(e) => setFormData({...formData, presentsTitle: e.target.value})}
              disabled={isViewMode}
            />
            <div className="coupon-counter-row">
              <div className="counter-control" style={formData.isDirectInput ? { padding: 0, border: 'none' } : {}}>
                {formData.isDirectInput ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {isViewMode ? (
                      <span className="counter-value">{formData.presentsCount} 개</span>
                    ) : (
                      <>
                        <input 
                          type="number" 
                          className="form-input-line" 
                          style={{ width: '80px', textAlign: 'center', padding: '0.5rem 0' }}
                          value={formData.presentsCount === 0 ? '' : formData.presentsCount}
                          onChange={(e) => setFormData({...formData, presentsCount: parseInt(e.target.value) || 0})}
                          min="0"
                        />
                        <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>개</span>
                      </>
                    )}
                  </div>
                ) : (
                  <>
                    {!isViewMode && (
                      <button className="counter-btn" onClick={() => setFormData({...formData, presentsCount: Math.max(0, formData.presentsCount - 1)})}>
                        <Minus size={16} />
                      </button>
                    )}
                    <span className="counter-value">{formData.presentsCount} 개</span>
                    {!isViewMode && (
                      <button className="counter-btn" onClick={() => setFormData({...formData, presentsCount: formData.presentsCount + 1})}>
                        <Plus size={16} />
                      </button>
                    )}
                  </>
                )}
              </div>
              {!isViewMode && (
                <div className="counter-actions">
                  <button 
                    className={`btn-outline-small ${formData.isUnlimited ? 'active' : ''}`}
                    onClick={() => handleBenefitValidation(() => setFormData({...formData, isUnlimited: !formData.isUnlimited, isDirectInput: false}))}
                  >
                    {t('coupon.btn_no_limit')}
                  </button>
                  <button 
                    className="btn-black-small"
                    style={formData.isDirectInput ? { backgroundColor: '#64748B', borderColor: '#64748B' } : {}}
                    onClick={() => handleBenefitValidation(() => setFormData({...formData, isDirectInput: !formData.isDirectInput, isUnlimited: false}))}
                  >
                    {t('coupon.btn_direct_input')}
                  </button>
                </div>
              )}
            </div>
            <div className="form-hint">{t('coupon.hint_presents')}</div>
          </div>
        </div>

        {/* Location */}
        <div className="form-group">
          <div className="form-label">{t('coupon.label_location')}</div>
          <div className="form-content">
            <div style={{ position: 'relative' }}>
              <input 
                type="text" 
                className="form-input-line" 
                placeholder={t('coupon.ph_location')}
                value={formData.location}
                onChange={(e) => setFormData({...formData, location: e.target.value})}
                disabled={isViewMode}
                style={{ paddingRight: '2.5rem' }}
              />
              <Search size={20} color="#94A3B8" style={{ position: 'absolute', right: '0.5rem', top: '50%', transform: 'translateY(-50%)' }} />
            </div>
            <div className="form-hint" style={{ marginTop: '0.5rem' }}>{t('coupon.hint_location')}</div>
          </div>
        </div>

        {/* Push */}
        <div className="form-group">
          <div className="form-label">{t('coupon.label_push')}</div>
          <div className="form-content">
            <div className="coupon-push-row">
              <label className="push-toggle-switch">
                <input 
                  type="checkbox" 
                  checked={formData.pushVisitors}
                  onChange={() => handlePushToggle('pushVisitors')}
                  disabled={isViewMode}
                />
                <span className="push-slider">
                  <span className="push-text">{formData.pushVisitors ? 'ON' : 'OFF'}</span>
                </span>
              </label>
              <span className="push-label">{t('coupon.push_visitors')}</span>
            </div>
            <div className="form-hint">{t('coupon.hint_push_visitors')}</div>

            <div className="coupon-push-row" style={{ marginTop: '1.5rem' }}>
              <label className="push-toggle-switch">
                <input 
                  type="checkbox" 
                  checked={formData.pushAll}
                  onChange={() => handlePushToggle('pushAll')}
                  disabled={isViewMode}
                />
                <span className="push-slider">
                  <span className="push-text">{formData.pushAll ? 'ON' : 'OFF'}</span>
                </span>
              </label>
              <span className="push-label">{t('coupon.push_all')}</span>
            </div>
            <div className="form-hint">{t('coupon.hint_push_all')}</div>
          </div>
        </div>

      </div>

      <BottomActionBar>
        {isViewMode ? (
          <>
            <Button variant="outline" fullWidth onClick={() => navigate('/dashboard/coupons')}>
              닫기
            </Button>
            <Button variant="primary" fullWidth onClick={() => navigate(`/dashboard/coupons/edit/${id || 1}`)}>
              수정
            </Button>
          </>
        ) : (
          <>
            <Button variant="outline" fullWidth onClick={() => navigate('/dashboard/coupons')}>
              취소
            </Button>
            <Button variant="primary" fullWidth onClick={handleSave}>
              저장
            </Button>
          </>
        )}
      </BottomActionBar>

      <ConfirmModal 
        isOpen={modalState.isOpen}
        desc={modalState.message}
        onConfirm={closeModalAndGoBack}
        singleButton={true}
      />

      <ConfirmModal 
        isOpen={showLimitModal}
        desc={limitMsg}
        onConfirm={() => setShowLimitModal(false)}
        onCancel={() => setShowLimitModal(false)}
        confirmText="구매하기"
        cancelText="닫기"
      />
    </div>
  );
};

export default CouponForm;
