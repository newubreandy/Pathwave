import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Ticket, Plus, ChevronRight, Info } from 'lucide-react';
import BottomActionBar from '../components/common/BottomActionBar';
import Button from '../components/common/Button';
import PwModal from '../components/common/PwModal.jsx';
import AuthService from '../services/auth/AuthService';
import CouponService from '../services/coupon/CouponService';
import '../pages/Stamps.css';
import './Notifications.css';

const Coupons = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [facilityId, setFacilityId] = useState(null);
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 사용 처리 모달 상태
  const [useModalCouponId, setUseModalCouponId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [doneModalOpen, setDoneModalOpen] = useState(false);

  // facility_id 로드 → 쿠폰 목록 로드
  const loadCoupons = useCallback(async (fid) => {
    setLoading(true);
    setError(null);
    try {
      const res = await CouponService.list(fid);
      setCoupons(res.data?.coupons ?? []);
    } catch (err) {
      setError('쿠폰 목록을 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    AuthService.me()
      .then((res) => {
        const fid = res?.facility_account?.facility_id ?? null;
        setFacilityId(fid);
        if (fid) loadCoupons(fid);
        else {
          setError('매장 정보를 찾을 수 없습니다.');
          setLoading(false);
        }
      })
      .catch(() => {
        setError('인증 정보를 불러오지 못했습니다.');
        setLoading(false);
      });
  }, [loadCoupons]);

  const openUseModal = (e, id) => {
    e.preventDefault();
    e.stopPropagation();
    setUseModalCouponId(id);
  };

  const confirmUse = async () => {
    if (!useModalCouponId || isProcessing) return;
    setIsProcessing(true);
    try {
      await CouponService.use(useModalCouponId);
      setUseModalCouponId(null);
      setDoneModalOpen(true);
      if (facilityId) loadCoupons(facilityId);
    } catch (err) {
      const msg = err?.response?.data?.message ?? '사용 처리에 실패했습니다.';
      alert(msg);
      setUseModalCouponId(null);
    } finally {
      setIsProcessing(false);
    }
  };

  const statusLabel = (status) => {
    if (status === 'active') return t('coupon.status_active', '쿠폰 진행 중');
    if (status === 'used') return t('coupon.used_label', '사용 완료');
    return t('coupon.status_ended', '쿠폰 진행 종료');
  };

  const expiresLabel = (coupon) => {
    if (coupon.expires_at) {
      const d = coupon.expires_at.slice(0, 10);
      return `사용기간 : ~ ${d}`;
    }
    return '사용기간 : 무기한';
  };

  return (
    <div className="stamps-page">
      <div className="page-header-section">
        <h1 className="page-title">{t('coupon.title_list', '쿠폰 관리')}</h1>
        <p className="sub-title">설치장소의 쿠폰을 관리합니다.</p>
      </div>

      {loading && (
        <div style={{ padding: 'var(--pw-space-8)', textAlign: 'center', color: 'var(--pw-text-hint)' }}>
          불러오는 중...
        </div>
      )}

      {!loading && error && (
        <div style={{ padding: 'var(--pw-space-8)', textAlign: 'center', color: 'var(--danger, #dc2626)' }}>
          {error}
        </div>
      )}

      {!loading && !error && coupons.length === 0 && (
        <div style={{ padding: 'var(--pw-space-8)', textAlign: 'center', color: 'var(--pw-text-hint)' }}>
          발급된 쿠폰이 없습니다.
        </div>
      )}

      {!loading && !error && coupons.length > 0 && (
        <div className="stamp-list">
          {coupons.map((coupon) => (
            <Link to={`/dashboard/coupons/view/${coupon.id}`} key={coupon.id} className="stamp-card">
              <div className={`stamp-icon ${coupon.status}`}>
                <Ticket size={24} />
              </div>
              <div className="stamp-info">
                <div className="stamp-info-head">
                  <h3 className="stamp-name" style={coupon.status !== 'active' ? { color: 'var(--pw-text-hint)' } : {}}>
                    {coupon.title}
                  </h3>
                  <span className={`stamp-status ${coupon.status}`}>
                    {statusLabel(coupon.status)}
                  </span>
                </div>
                <div className="stamp-details">
                  <div>{expiresLabel(coupon)}</div>
                  {coupon.benefit && <div style={{ marginTop: '2px', color: 'var(--pw-text-hint)' }}>{coupon.benefit}</div>}
                </div>
                {/* 사용 처리 액션 — active 쿠폰만 노출 */}
                {coupon.status === 'active' && (
                  <button
                    className="coupon-use-btn"
                    onClick={(e) => openUseModal(e, coupon.id)}
                    style={{
                      marginTop: 'var(--pw-space-3)',
                      padding: 'var(--pw-space-2) var(--pw-space-4)',
                      background: 'var(--pw-accent-soft)',
                      border: '1px solid var(--pw-accent)',
                      borderRadius: 'var(--pw-radius-sm)',
                      color: 'var(--pw-accent-text)',
                      fontSize: 'var(--pw-caption-size)',
                      fontWeight: 600,
                      cursor: 'pointer',
                      width: 'fit-content',
                      transition: 'background var(--pw-duration-fast) var(--pw-ease)'
                    }}
                  >
                    {t('coupon.staff_use_btn', '사용 처리')}
                  </button>
                )}
              </div>
              <ChevronRight className="stamp-arrow" size={20} />
            </Link>
          ))}
        </div>
      )}

      <BottomActionBar>
        <Button
          variant="primary"
          fullWidth
          icon={<Plus size={18} />}
          onClick={() => navigate('/dashboard/coupons/add')}
        >
          쿠폰 발급
        </Button>
      </BottomActionBar>

      {/* 사용 처리 확인 모달 */}
      <PwModal
        open={!!useModalCouponId}
        onClose={() => !isProcessing && setUseModalCouponId(null)}
        title={t('coupon.staff_use_title', '쿠폰 사용 처리')}
        busy={isProcessing}
        size="sm"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setUseModalCouponId(null)}
              disabled={isProcessing}
            >
              {t('noti.btn_cancel', '취소')}
            </Button>
            <Button
              variant="primary"
              onClick={confirmUse}
              disabled={isProcessing}
            >
              {isProcessing ? '처리 중...' : t('coupon.staff_use_btn', '사용 처리')}
            </Button>
          </>
        }
      >
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          alignItems: 'flex-start',
          background: 'rgba(245, 158, 11, 0.10)',
          border: '1px solid rgba(245, 158, 11, 0.35)',
          borderRadius: 'var(--pw-radius-sm)',
          padding: '0.75rem 1rem',
          color: '#F59E0B',
          fontSize: 'var(--pw-caption-size)',
          lineHeight: '1.6',
          textAlign: 'left',
        }}>
          <Info size={14} style={{ flexShrink: 0, marginTop: '2px' }} />
          <span>
            쿠폰 #{useModalCouponId}을 사용 처리하시겠습니까?{'\n'}
            {t('coupon.staff_use_warning', '실제 매장에서 혜택을 제공한 후에만 처리하세요. 사용 처리는 되돌릴 수 없습니다.')}
          </span>
        </div>
      </PwModal>

      {/* 사용 처리 완료 모달 */}
      <PwModal
        open={doneModalOpen}
        onClose={() => setDoneModalOpen(false)}
        title={t('coupon.staff_use_title', '쿠폰 사용 처리')}
        size="sm"
        footer={
          <Button variant="primary" fullWidth onClick={() => setDoneModalOpen(false)}>
            {t('noti.btn_confirm', '확인')}
          </Button>
        }
      >
        <p style={{ textAlign: 'center', color: 'var(--pw-text-secondary)', margin: 0 }}>
          {t('coupon.staff_use_done', '쿠폰 사용 처리가 완료되었습니다.')}
        </p>
      </PwModal>
    </div>
  );
};

export default Coupons;
