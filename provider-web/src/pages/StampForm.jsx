import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, ChevronLeft, Minus, Plus, X } from 'lucide-react';
import StampService from '../services/stamp/StampService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import './StampForm.css';



const StampForm = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { action, id } = useParams(); // 'new', 'edit', 'view'
  const isViewMode = action === 'view';


  const getTodayStr = () => new Date().toISOString().split('T')[0];

  const [formData, setFormData] = useState({
    name: '',
    accumStart: getTodayStr(),
    accumEnd: '9999-12-31',
    paymentAmount: 5000,
    isDirectInput: false,
    benefits: [
      { id: 1, count: '10회차', desc: '5,000원 할인' }
    ]
  });

  const [modalState, setModalState] = useState({
    isOpen: false,
    title: '',
    desc: '',
    type: 'alert', // 'alert' or 'confirm'
    onConfirm: () => {},
  });

  const closeModal = () => {
    setModalState(prev => ({ ...prev, isOpen: false }));
  };

  const showAlert = (desc, onConfirmCallback = closeModal) => {
    setModalState({
      isOpen: true,
      title: '',
      desc,
      type: 'alert',
      onConfirm: onConfirmCallback
    });
  };

  const showConfirmModal = (title, desc, onConfirmCallback) => {
    setModalState({
      isOpen: true,
      title,
      desc,
      type: 'confirm',
      onConfirm: () => {
        onConfirmCallback();
        closeModal();
      }
    });
  };

  // Mock initial load for edit
  useEffect(() => {
    const loadStampData = async () => {
      if (action === 'edit' || action === 'view') {
        if (id) {
          try {
            const stamp = await StampService.getStampById(id);
            const [accumStart, accumEnd] = stamp.period.split(' - ');
            setFormData({
              name: stamp.name,
              accumStart: accumStart || getTodayStr(),
              accumEnd: accumEnd || '9999-12-31',
              paymentAmount: 5000,
              benefits: [
                { id: 1, count: '10회차', desc: stamp.benefit }
              ]
            });
          } catch (error) {
            showAlert('스탬프 정보를 불러오지 못했습니다.', () => navigate('/dashboard/stamps'));
          }
        }
      } else {
        // Show pass purchase modal on new creation to simulate the flow
        showConfirmModal(
          t('stamp.modal_pass_title', '스탬프 이용권 구매'),
          t('stamp.modal_pass_desc', '이용권이 없어 스탬프 기능을 이용할 수 없습니다.\n스탬프 이용권을 구매하시겠습니까?'),
          () => closeModal() // Normally would redirect to purchase
        );
      }
    };
    loadStampData();
  }, [action, id]);


  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleBenefitChange = (id, field, value) => {
    setFormData(prev => ({
      ...prev,
      benefits: prev.benefits.map(b => b.id === id ? { ...b, [field]: value } : b)
    }));
  };

  const removeBenefit = (id) => {
    if (formData.benefits.length <= 1) {
      showAlert('최소 1개 이상의 혜택이 등록되어야 합니다.');
      return;
    }
    if (formData.benefits.length === 1) {
      setFormData({...formData, benefits: [{ id: formData.benefits[0].id, count: '', desc: '' }]});
      return;
    }
    setFormData({...formData, benefits: formData.benefits.filter(b => b.id !== id)});
  };

  const addBenefit = () => {
    if (formData.benefits.length >= 4) {
      showAlert(t('stamp.alert_max_benefits', '혜택조건은 최대 4회입니다.'));
      return;
    }
    const newId = Date.now();
    setFormData(prev => ({
      ...prev,
      benefits: [...prev.benefits, { id: newId, count: '', desc: '' }]
    }));
  };

  const validate = () => {
    if (!formData.name) {
      showAlert(t('stamp.alert_missing_field', "'스탬프명'을(를) 등록해 주세요.").replace('{{field}}', '스탬프명'));
      return false;
    }

    if (new Date(formData.accumStart) < new Date(new Date().setHours(0, 0, 0, 0))) {
      showAlert(t('stamp.alert_date_past', '시작기간은 과거로 설정할 수 없습니다.'));
      return false;
    }

    if (new Date(formData.accumStart) > new Date(formData.accumEnd)) {
      showAlert(t('stamp.alert_date_logic', '시작일은 종료일보다 빠를 수 없습니다.'));
      return false;
    }

    if (formData.benefits.length === 0 || !formData.benefits[0].count || !formData.benefits[0].desc) {
      showAlert(t('stamp.alert_no_benefit', '최소 1개 이상의 혜택이 등록되어야 합니다.'));
      return false;
    }

    return true;
  };

  const handleSave = () => {
    if (!validate()) return;

    showConfirmModal(
      '',
      t('stamp.modal_issue_desc', '발행된 스탬프는 기간내 종료 또는 수정할 수 없습니다.\n해당 내역으로 스탬프 혜택을 발행하시겠습니까?'),
      async () => {
        try {
          await StampService.createStamp({
            title: formData.name,
            startDate: formData.accumStart,
            endDate: formData.accumEnd,
            benefits: formData.benefits.map(b => ({ item: b.desc }))
          });
          showAlert(t('stamp.alert_save_success', '저장이 완료되었습니다.'), () => navigate('/dashboard/stamps'));
        } catch (error) {
          showAlert(error.message);
        }
      }
    );
  };

  return (
    <div className="common-form-page">
      <div className="common-form-header">
        <button className="back-btn" onClick={() => navigate('/dashboard/stamps')}>
          <ChevronLeft size={24} />
        </button>
        <h1>
          {action === 'new' && t('stamp.title_add', '스탬프 등록')}
          {action === 'edit' && '스탬프 수정'}
          {action === 'view' && t('stamp.title_view', '스탬프 상세')}
        </h1>
      </div>

      <div className="form-group">
        <label className="form-label">스탬프명</label>
        <div className="form-content">
          <input 
            type="text" 
            className="form-input" 
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder={t('stamp.ph_name', '스탬프로 사용할 이름을 입력하세요')} 
            disabled={isViewMode}
          />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">스탬프 적립/사용 기간</label>
        <div className="form-content">
          <div className="date-range-group">
            <input type="date" className="date-input" name="accumStart" value={formData.accumStart} onChange={handleChange} disabled={isViewMode} />
            <span className="date-separator">~</span>
            <input type="date" className="date-input" name="accumEnd" value={formData.accumEnd} onChange={handleChange} disabled={isViewMode} max="9999-12-31" />
          </div>
          <div className="form-hint">{t('stamp.hint_accumulation_period', '※ 스탬프 적립 및 혜택이 적용되는 기간입니다.')}</div>
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">결제기준금액</label>
        <div className="form-content">
          <div className="coupon-counter-row" style={{ marginTop: 0, justifyContent: 'space-between', padding: '0.875rem 0' }}>
            <div className="counter-control" style={formData.isDirectInput ? { padding: 0, border: 'none' } : {}}>
              {formData.isDirectInput ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {isViewMode ? (
                    <span className="counter-value">{formData.paymentAmount.toLocaleString()}원</span>
                  ) : (
                    <>
                      <input 
                        type="number" 
                        className="form-input" 
                        style={{ width: '100px', textAlign: 'center', padding: '0.5rem 0' }}
                        value={formData.paymentAmount === 0 ? '' : formData.paymentAmount}
                        onChange={(e) => setFormData({...formData, paymentAmount: parseInt(e.target.value) || 0})}
                        min="0"
                      />
                      <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>원</span>
                    </>
                  )}
                </div>
              ) : (
                <>
                  {!isViewMode && (
                    <button className="counter-btn" onClick={() => setFormData(prev => ({...prev, paymentAmount: Math.max(0, prev.paymentAmount - 1000)}))}>
                      <Minus size={16} />
                    </button>
                  )}
                  <span className="counter-value" style={{ minWidth: '80px' }}>{formData.paymentAmount.toLocaleString()}원</span>
                  {!isViewMode && (
                    <button className="counter-btn" onClick={() => setFormData(prev => ({...prev, paymentAmount: prev.paymentAmount + 1000}))}>
                      <Plus size={16} />
                    </button>
                  )}
                </>
              )}
            </div>
            {!isViewMode && (
              <div className="counter-actions">
                <button 
                  className="btn-black-small"
                  style={formData.isDirectInput ? { backgroundColor: '#64748B', borderColor: '#64748B' } : {}}
                  onClick={() => setFormData({...formData, isDirectInput: !formData.isDirectInput})}
                >
                  직접입력
                </button>
              </div>
            )}
          </div>
          <div className="form-hint">
            {t('stamp.hint_payment1', '※ 스탬프 1개가 적립될 결제금액을 입력하세요.')}<br/>
            {t('stamp.hint_payment2', '※ 스탬프 자동수동은 결제금액을 총 결제금액/단건 나눔 횟수 만큼 적립됩니다.')}<br/>
            {t('stamp.hint_payment3', '예) 5,000원 설정 시 결제금액 4,000원 = 적립 불가\n5,000원 설정 시 결제금액 10,500원 = 2개 적립').split('\n').map((line, i) => <React.Fragment key={i}>{line}<br/></React.Fragment>)}
          </div>
        </div>
      </div>

      {formData.benefits.map((benefit, index) => (
        <div key={benefit.id} className="form-group benefit-group" style={{ position: 'relative', ...(index === formData.benefits.length - 1 && formData.benefits.length >= 4 ? { borderBottom: 'none' } : {}) }}>
          <label className="form-label">
            <span>혜택조건 {index + 1}</span>
          </label>
          <div className="form-content">
            <div className="benefit-item" style={{ position: 'relative' }}>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <input 
                  type="text" 
                  className="form-input" 
                  value={benefit.count} 
                  onChange={(e) => handleBenefitChange(benefit.id, 'count', e.target.value)} 
                  placeholder={t('stamp.ph_benefit_count', '10회차')} 
                  disabled={isViewMode}
                />
              </div>
              <div className="form-hint" style={{ marginBottom: '1rem' }}>※ 스탬프 적립완료 기준을 입력하세요</div>
              
              <input 
                type="text" 
                className="form-input" 
                value={benefit.desc} 
                onChange={(e) => handleBenefitChange(benefit.id, 'desc', e.target.value)} 
                placeholder={t('stamp.ph_benefit_desc', '5,000원 할인')} 
                disabled={isViewMode}
              />
              <div className="form-hint">※ 스탬프 적립완료 혜택을 입력하세요</div>
            </div>
          </div>
          {!isViewMode && (
            <button 
              type="button"
              className="btn-outline-small benefit-delete-absolute"
              onClick={() => removeBenefit(benefit.id)}
            >
              삭제 <X size={14} />
            </button>
          )}
        </div>
      ))}
      
      {formData.benefits.length < 4 && !isViewMode && (
        <div className="form-group" style={{ borderBottom: 'none' }}>
          <div style={{ textAlign: 'center', width: '100%', padding: '1rem 0' }}>
            <button 
              type="button"
              className="btn-black-small" 
              style={{ margin: '0 auto', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.2rem', fontSize: '0.95rem' }} 
              onClick={addBenefit}
            >
              <Plus size={16} /> 혜택추가
            </button>
          </div>
        </div>
      )}

      <BottomActionBar>
        {isViewMode ? (
          <>
            <Button variant="outline" fullWidth onClick={() => navigate('/dashboard/stamps')}>
              닫기
            </Button>
            <Button variant="primary" fullWidth onClick={() => navigate(`/dashboard/stamps/edit/${id}`)}>
              수정
            </Button>
          </>
        ) : (
          <>
            <Button variant="outline" fullWidth onClick={() => navigate('/dashboard/stamps')}>
              {t('stamp.btn_cancel', '취소')}
            </Button>
            <Button variant="primary" fullWidth onClick={handleSave}>
              {t('stamp.btn_save', '저장')}
            </Button>
          </>
        )}
      </BottomActionBar>

      <ConfirmModal 
        isOpen={modalState.isOpen}
        title={modalState.title}
        desc={modalState.desc}
        onConfirm={modalState.onConfirm}
        onCancel={closeModal}
        singleButton={modalState.type === 'alert'}
      />
    </div>
  );
};

export default StampForm;
