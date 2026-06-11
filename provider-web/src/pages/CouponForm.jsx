import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChevronLeft, Trash2 } from 'lucide-react';
import BottomActionBar from '../components/common/BottomActionBar';
import Button from '../components/common/Button';
import ConfirmModal from '../components/common/ConfirmModal';
import AuthService from '../services/auth/AuthService';
import CouponService from '../services/coupon/CouponService';
import './CouponForm.css';

const CouponForm = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { action, id } = useParams(); // 'add', 'edit', 'view'

  const isViewMode = action === 'view';
  const isEditMode = action === 'edit' && !!id;
  const isAddMode  = action === 'add';

  const [facilityId, setFacilityId] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    benefit: '',
    validityDays: '',
    userId: '',      // 단건 발급 시 회원 번호
  });
  const [loadError, setLoadError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const submittingRef = useRef(false);

  const [modalState, setModalState] = useState({ isOpen: false, message: '' });
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showDeleteDone, setShowDeleteDone] = useState(false);

  // facility_id 로드
  useEffect(() => {
    AuthService.me()
      .then((res) => {
        const fid = res?.facility_account?.facility_id ?? null;
        setFacilityId(fid);
      })
      .catch(() => setLoadError('인증 정보를 불러오지 못했습니다.'));
  }, []);

  // 수정/조회 시 기존 쿠폰 로드
  useEffect(() => {
    if (!id || isAddMode) return;
    CouponService.get(id)
      .then((res) => {
        const c = res.data?.coupon;
        if (!c) return;
        setFormData({
          title:       c.title ?? '',
          benefit:     c.benefit ?? '',
          validityDays: '',  // expires_at 역산 불필요 — 조회 전용 표시
          userId:      String(c.user_id ?? ''),
        });
      })
      .catch(() => setLoadError('쿠폰 정보를 불러오지 못했습니다.'));
  }, [id, isAddMode]);

  // validityDays(N일) → ISO expires_at 변환
  const buildExpiresAt = (days) => {
    const n = parseInt(days, 10);
    if (!n || n <= 0) return undefined;
    const d = new Date();
    d.setDate(d.getDate() + n);
    // ISO 8601 날짜 문자열 (시각 없이 날짜만 전달해도 backend fromisoformat 통과)
    return d.toISOString().slice(0, 10);
  };

  const handleSave = async () => {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setSubmitting(true);

    try {
      if (isAddMode) {
        // 발급: title 필수, user_id 필수
        const title = formData.title.trim();
        const uid = parseInt(formData.userId, 10);
        if (!title) {
          alert('쿠폰 이름을 입력하세요.');
          return;
        }
        if (!uid || uid <= 0) {
          alert('회원 번호를 올바르게 입력하세요.');
          return;
        }
        if (!facilityId) {
          alert('매장 정보를 불러오지 못했습니다. 새로고침 후 다시 시도하세요.');
          return;
        }

        const payload = {
          title,
          user_id: uid,
        };
        if (formData.benefit.trim()) payload.benefit = formData.benefit.trim();
        const expiresAt = buildExpiresAt(formData.validityDays);
        if (expiresAt) payload.expires_at = expiresAt;

        await CouponService.issue(facilityId, payload);
        setModalState({ isOpen: true, message: '쿠폰이 발급되었습니다.' });

      } else if (isEditMode) {
        // 수정: title/benefit/expires_at 만 허용
        const patch = {};
        const title = formData.title.trim();
        if (title) patch.title = title;
        patch.benefit = formData.benefit.trim() || null;
        const expiresAt = buildExpiresAt(formData.validityDays);
        if (expiresAt) patch.expires_at = expiresAt;

        if (Object.keys(patch).length === 0) {
          alert('수정할 내용이 없습니다.');
          return;
        }

        await CouponService.update(id, patch);
        setModalState({ isOpen: true, message: t('coupon.msg_saved', '이벤트가 수정되었습니다.') });
      }
    } catch (err) {
      const msg = err?.response?.data?.message ?? '저장에 실패했습니다.';
      alert(msg);
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    setShowDeleteConfirm(false);
    try {
      await CouponService.remove(id);
      setShowDeleteDone(true);
    } catch (err) {
      const msg = err?.response?.data?.message ?? '삭제에 실패했습니다.';
      alert(msg);
    }
  };

  const closeModalAndGoBack = () => {
    setModalState({ isOpen: false, message: '' });
    navigate('/dashboard/coupons');
  };

  if (loadError) {
    return (
      <div className="common-form-page">
        <div style={{ padding: 'var(--pw-space-8)', textAlign: 'center', color: 'var(--danger, #dc2626)' }}>
          {loadError}
        </div>
      </div>
    );
  }

  return (
    <div className="common-form-page">
      <div className="common-form-header">
        <button className="back-btn" onClick={() => navigate('/dashboard/coupons')}>
          <ChevronLeft size={24} />
        </button>
        <h1>{isViewMode ? t('coupon.title_view', '쿠폰 상세') : isEditMode ? t('coupon.title_edit', '쿠폰 수정') : t('coupon_issue.form_title', '쿠폰 발급')}</h1>
      </div>

      <div className="coupon-form-container">

        {/* 쿠폰 이름 */}
        <div className="form-group">
          <div className="form-label">{t('coupon.label_title', '쿠폰 이름')} <span style={{ color: 'var(--danger, #dc2626)' }}>*</span></div>
          <div className="form-content">
            <input
              type="text"
              className="form-input-line"
              placeholder={t('coupon.ph_title', '예) 아메리카노 무료 쿠폰')}
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              disabled={isViewMode}
            />
          </div>
        </div>

        {/* 혜택 내용 */}
        <div className="form-group">
          <div className="form-label">{t('coupon_issue.form_benefit_label', '혜택 내용')}</div>
          <div className="form-content">
            <input
              type="text"
              className="form-input-line"
              placeholder={t('coupon.ph_presents', '쿠폰 혜택을 입력하세요')}
              value={formData.benefit}
              onChange={(e) => setFormData({ ...formData, benefit: e.target.value })}
              disabled={isViewMode}
            />
          </div>
        </div>

        {/* 유효기간 */}
        {!isViewMode && (
          <div className="form-group">
            <div className="form-label">{t('coupon_issue.form_validity_label', '유효기간 (일)')}</div>
            <div className="form-content">
              <input
                type="number"
                className="form-input-line"
                placeholder="30"
                value={formData.validityDays}
                onChange={(e) => setFormData({ ...formData, validityDays: e.target.value })}
                min="1"
              />
              <div className="form-hint">{t('coupon_issue.form_validity_hint', '※ 발급일로부터 N일 동안 사용 가능합니다. 비워두면 무기한 — 30~90일 권장.')}</div>
            </div>
          </div>
        )}

        {/* 단건 발급: 회원 번호 입력 */}
        {isAddMode && (
          <div className="form-group">
            <div className="form-label">
              {t('coupon_issue.form_user_label', '회원 번호')} <span style={{ color: 'var(--danger, #dc2626)' }}>*</span>
            </div>
            <div className="form-content">
              <input
                type="number"
                className="form-input-line"
                placeholder={t('coupon_issue.form_user_placeholder', 'QR 또는 번호로 확인한 회원 번호')}
                value={formData.userId}
                onChange={(e) => setFormData({ ...formData, userId: e.target.value })}
                min="1"
              />
              <div className="form-hint">{t('coupon_issue.form_user_hint', '※ 사용자가 제시한 QR 코드 또는 회원 번호를 입력하세요.')}</div>
            </div>
          </div>
        )}

      </div>

      {!isViewMode && (
        <div style={{
          backgroundColor: 'rgba(234, 179, 8, 0.15)',
          border: '1px solid rgba(234, 179, 8, 0.5)',
          borderRadius: 'var(--pw-radius-sm)',
          padding: 'var(--pw-space-4)',
          marginTop: 'var(--pw-space-6)',
          marginBottom: 'var(--pw-space-4)',
          fontSize: 'var(--pw-caption-size)',
          color: '#ca8a04',
          lineHeight: 'var(--pw-body-leading)',
        }}>
          {t('coupon_issue.form_compliance', '발급 후 쿠폰의 혜택 조건·유효기간·사용 제한을 변경할 수 없습니다. 조건 변경이 필요한 경우 새 쿠폰을 발급하세요.')}
        </div>
      )}

      <BottomActionBar>
        {isViewMode ? (
          <>
            <Button variant="outline" fullWidth onClick={() => navigate('/dashboard/coupons')}>
              닫기
            </Button>
            <Button variant="primary" fullWidth onClick={() => navigate(`/dashboard/coupons/edit/${id}`)}>
              수정
            </Button>
          </>
        ) : isEditMode ? (
          <>
            <Button
              variant="outline"
              fullWidth
              icon={<Trash2 size={18} />}
              onClick={() => setShowDeleteConfirm(true)}
              style={{ color: 'var(--danger, #dc2626)', borderColor: 'var(--danger, #dc2626)' }}
            >
              삭제
            </Button>
            <Button variant="outline" fullWidth onClick={() => navigate('/dashboard/coupons')}>
              취소
            </Button>
            <Button variant="primary" fullWidth onClick={handleSave} disabled={submitting}>
              {submitting ? '저장 중...' : '저장'}
            </Button>
          </>
        ) : (
          <>
            <Button variant="outline" fullWidth onClick={() => navigate('/dashboard/coupons')}>
              취소
            </Button>
            <Button variant="primary" fullWidth onClick={handleSave} disabled={submitting}>
              {submitting ? '발급 중...' : '발급'}
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

      {/* 삭제 확인 */}
      <ConfirmModal
        isOpen={showDeleteConfirm}
        desc={'이 쿠폰을 삭제하시겠습니까?\n삭제된 쿠폰은 복구할 수 없습니다.'}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
        confirmText="삭제"
        cancelText="취소"
      />

      {/* 삭제 완료 */}
      <ConfirmModal
        isOpen={showDeleteDone}
        desc={'쿠폰이 삭제되었습니다.'}
        onConfirm={() => {
          setShowDeleteDone(false);
          navigate('/dashboard/coupons');
        }}
        singleButton={true}
      />
    </div>
  );
};

export default CouponForm;
