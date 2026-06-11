import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import StampService from '../services/stamp/StampService';
import AuthService from '../services/auth/AuthService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import './StampForm.css';

const StampForm = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { action, id } = useParams(); // 'new', 'edit', 'view'
  const isViewMode = action === 'view';

  const [facilityId, setFacilityId] = useState(null);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    reward_description: '',
    reward_threshold: 10,
    expiresDays: '',
    autoStamp: false,
    cooldownMinutes: 60,
  });

  const [modalState, setModalState] = useState({
    isOpen: false,
    title: '',
    desc: '',
    type: 'alert',
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
      onConfirm: onConfirmCallback,
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
      },
    });
  };

  // fid 확보 후 edit/view 진입 시 데이터 로드
  useEffect(() => {
    AuthService.me()
      .then((res) => {
        const fid = res?.facility_account?.facility_id ?? null;
        setFacilityId(fid);
        if ((action === 'edit' || action === 'view') && fid) {
          loadPolicy(fid);
        }
      })
      .catch(() => {
        showAlert('사용자 정보를 불러오지 못했습니다.', () => navigate('/dashboard/stamps'));
      });
  }, [action]);

  const loadPolicy = async (fid) => {
    try {
      const res = await StampService.get(fid);
      const policy = res?.policy ?? null;
      if (policy) {
        setFormData({
          reward_description: policy.reward_description ?? '',
          reward_threshold: policy.reward_threshold ?? 10,
          expiresDays: policy.expires_days ? String(policy.expires_days) : '',
          autoStamp: !!policy.auto_stamp_enabled,
          cooldownMinutes: policy.auto_stamp_cooldown_minutes ?? 60,
        });
      } else {
        showAlert('스탬프 정보를 불러오지 못했습니다.', () => navigate('/dashboard/stamps'));
      }
    } catch (error) {
      showAlert('스탬프 정보를 불러오지 못했습니다.', () => navigate('/dashboard/stamps'));
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const validate = () => {
    if (!formData.reward_description.trim()) {
      showAlert('보상 내용을 입력해 주세요.');
      return false;
    }
    const threshold = Number(formData.reward_threshold);
    if (!threshold || threshold < 1) {
      showAlert('목표 회차는 1 이상의 숫자를 입력해 주세요.');
      return false;
    }
    return true;
  };

  const handleSave = () => {
    if (!validate()) return;

    showConfirmModal(
      '',
      '저장하면 기존 활성 정책이 대체됩니다. 계속하시겠습니까?',
      async () => {
        if (saving) return;
        setSaving(true);
        try {
          const payload = {
            reward_threshold: Number(formData.reward_threshold),
            reward_description: formData.reward_description.trim(),
            auto_stamp_enabled: formData.autoStamp,
          };
          const expiresDays = Number(formData.expiresDays);
          if (expiresDays >= 1) payload.expires_days = expiresDays;

          const cooldown = Number(formData.cooldownMinutes);
          if (cooldown >= 1) payload.auto_stamp_cooldown_minutes = cooldown;

          await StampService.save(facilityId, payload);
          showAlert(t('stamp.alert_save_success', '저장이 완료되었습니다.'), () => navigate('/dashboard/stamps'));
        } catch (error) {
          showAlert(error.message || '저장에 실패했습니다. 잠시 후 다시 시도해 주세요.');
        } finally {
          setSaving(false);
        }
      }
    );
  };

  return (
    <div className="common-form-page">
      <div className="common-form-header">
        <button className="back-btn" aria-label="뒤로 가기" onClick={() => navigate('/dashboard/stamps')}>
          <ChevronLeft size={24} />
        </button>
        <h1>
          {action === 'new' && t('stamp.policy_title', '스탬프 정책 설정')}
          {action === 'edit' && t('stamp.policy_title', '스탬프 정책 설정')}
          {action === 'view' && t('stamp.title_view', '스탬프 상세')}
        </h1>
      </div>

      {!isViewMode && (
        <div style={{
          backgroundColor: 'rgba(234, 179, 8, 0.15)',
          border: '1px solid rgba(234, 179, 8, 0.5)',
          borderRadius: 'var(--pw-radius-sm)',
          padding: 'var(--pw-space-4)',
          marginBottom: 'var(--pw-space-6)',
          fontSize: 'var(--pw-caption-size)',
          color: '#ca8a04',
          lineHeight: 'var(--pw-body-leading)',
        }}>
          {t('stamp.policy_single_active', '매장당 활성 스탬프 정책은 1개만 유지됩니다. 새 정책을 저장하면 기존 정책이 자동으로 비활성화됩니다.')}
        </div>
      )}

      {/* 보상 내용 */}
      <div className="form-group">
        <label className="form-label">보상 내용</label>
        <div className="form-content">
          <input
            type="text"
            className="form-input"
            name="reward_description"
            value={formData.reward_description}
            onChange={handleChange}
            placeholder="예) 아메리카노 1잔 무료"
            disabled={isViewMode}
          />
          <div className="form-hint">※ 목표 회차 달성 시 제공되는 보상 내용을 입력하세요.</div>
        </div>
      </div>

      {/* 목표 회차 */}
      <div className="form-group">
        <label className="form-label">목표 회차</label>
        <div className="form-content">
          <input
            type="number"
            className="form-input"
            name="reward_threshold"
            value={formData.reward_threshold}
            onChange={handleChange}
            min="1"
            disabled={isViewMode}
          />
          <div className="form-hint">※ 스탬프 N개 적립 시 보상이 지급됩니다. 최소 1 이상.</div>
        </div>
      </div>

      {/* 스탬프 유효기간 (일) */}
      <div className="form-group">
        <label className="form-label">스탬프 유효기간 (일)</label>
        <div className="form-content">
          <input
            type="number"
            className="form-input"
            name="expiresDays"
            value={formData.expiresDays}
            onChange={handleChange}
            min="1"
            placeholder="비워두면 무기한"
            disabled={isViewMode}
          />
          <div className="form-hint">{t('stamp.policy_expires_hint', '※ 적립된 스탬프의 유효 기간(일)입니다. 0 = 무기한.')}</div>
        </div>
      </div>

      {/* BLE 자동 적립 토글 */}
      <div className="form-group">
        <label className="form-label">{t('stamp.policy_auto_label', 'BLE 비콘 자동 적립')}</label>
        <div className="form-content">
          <div className="coupon-push-row">
            <label className="push-toggle-switch">
              <input
                type="checkbox"
                checked={formData.autoStamp}
                onChange={() => !isViewMode && setFormData(prev => ({ ...prev, autoStamp: !prev.autoStamp }))}
                disabled={isViewMode}
              />
              <span className="push-slider">
                <span className="push-text">{formData.autoStamp ? 'ON' : 'OFF'}</span>
              </span>
            </label>
          </div>
          <div className="form-hint">{t('stamp.policy_auto_hint', '※ ON: 고객이 비콘 범위에 입장하면 자동으로 스탬프 적립.\n※ OFF: 점주가 회원 QR 을 스캔해서 수동 적립 (점주 모드).')}</div>
        </div>
      </div>

      {/* 쿨다운 (분) */}
      <div className="form-group">
        <label className="form-label">쿨다운 (분)</label>
        <div className="form-content">
          <input
            type="number"
            className="form-input"
            name="cooldownMinutes"
            value={formData.cooldownMinutes}
            onChange={handleChange}
            min="1"
            disabled={isViewMode}
          />
          <div className="form-hint">{t('stamp.policy_cooldown_hint', '※ 동일 고객의 중복 적립을 방지하는 최소 간격(분)입니다. 0 = 제한 없음.')}</div>
        </div>
      </div>

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
            <Button variant="primary" fullWidth onClick={handleSave} disabled={saving}>
              {saving ? '저장 중...' : t('stamp.btn_save', '저장')}
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
