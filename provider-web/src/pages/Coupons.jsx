import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Ticket, Plus, ChevronRight, Info } from 'lucide-react';
import BottomActionBar from '../components/common/BottomActionBar';
import Button from '../components/common/Button';
import '../pages/Stamps.css'; // 쿠폰/스탬프 리스트는 동일 카드 스타일 공유
import './Notifications.css'; // modal-overlay / modal-content / modal-btn 공통 스타일

const Coupons = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [coupons, setCoupons] = useState([
    {
      id: 1,
      name: '호텔H 썬베드 선착순 50명 무료 이용권 증정쿠폰',
      period: '2022.05.01 ~ 2022.05.31',
      status: 'active'
    },
    {
      id: 2,
      name: '아메리카노 무료 증정 쿠폰',
      period: '2022.04.01 ~ 2022.04.30',
      status: 'ended'
    },
    {
      id: 3,
      name: '썬베드 무료이용권 (사용완료)',
      period: '2022.03.01 ~ 2022.03.31',
      status: 'used'
    }
  ]);

  // 사용 처리 모달 상태
  const [useModalCouponId, setUseModalCouponId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [doneModalOpen, setDoneModalOpen] = useState(false);

  const openUseModal = (e, id) => {
    e.preventDefault(); // Link 탐색 방지
    e.stopPropagation();
    setUseModalCouponId(id);
  };

  const confirmUse = async () => {
    if (!useModalCouponId) return;
    setIsProcessing(true);
    try {
      // POST /api/coupons/<cid>/use — 실 연동 시 fetch 교체
      await fetch(`/api/coupons/${useModalCouponId}/use`, { method: 'POST' }).catch(() => {});
    } finally {
      setCoupons(prev =>
        prev.map(c => c.id === useModalCouponId ? { ...c, status: 'used' } : c)
      );
      setIsProcessing(false);
      setUseModalCouponId(null);
      setDoneModalOpen(true);
    }
  };

  const statusLabel = (status) => {
    if (status === 'active') return t('coupon.status_active', '쿠폰 진행 중');
    if (status === 'used') return t('coupon.used_label', '사용 완료');
    return t('coupon.status_ended', '쿠폰 진행 종료');
  };

  return (
    <div className="stamps-page">
      <div className="page-header-section">
        <h1 className="page-title">{t('coupon.title_list', '쿠폰 관리')}</h1>
        <p className="sub-title">설치장소의 쿠폰을 관리합니다.</p>
      </div>

      <div className="stamp-list">
        {coupons.map((coupon) => (
          <Link to={`/dashboard/coupons/view/${coupon.id}`} key={coupon.id} className="stamp-card">
            <div className={`stamp-icon ${coupon.status}`}>
              <Ticket size={24} />
            </div>
            <div className="stamp-info">
              <div className="stamp-info-head">
                <h3 className="stamp-name" style={coupon.status === 'used' ? { color: 'var(--pw-text-hint)' } : {}}>
                  {coupon.name}
                </h3>
                <span className={`stamp-status ${coupon.status}`}>
                  {statusLabel(coupon.status)}
                </span>
              </div>
              <div className="stamp-details">
                <div>사용기간 : {coupon.period}</div>
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

      <BottomActionBar>
        <Button
          variant="primary"
          fullWidth
          icon={<Plus size={18} />}
          onClick={() => navigate('/dashboard/service-request?type=event')}
        >
          쿠폰 등록
        </Button>
      </BottomActionBar>

      {/* 사용 처리 확인 모달 */}
      {useModalCouponId && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2 style={{ fontSize: '1.1rem', margin: '1.5rem 0 0.5rem', color: 'var(--pw-text)', padding: '0 1.5rem' }}>
              {t('coupon.staff_use_title', '쿠폰 사용 처리')}
            </h2>
            <div className="modal-body" style={{ paddingTop: '0.75rem' }}>
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
                marginBottom: '0.5rem'
              }}>
                <Info size={14} style={{ flexShrink: 0, marginTop: '2px' }} />
                <span>{t('coupon.staff_use_warning', '실제 매장에서 혜택을 제공한 후에만 처리하세요. 사용 처리는 되돌릴 수 없습니다.')}</span>
              </div>
            </div>
            <div className="modal-actions">
              <button
                className="modal-btn cancel"
                onClick={() => setUseModalCouponId(null)}
                disabled={isProcessing}
              >
                {t('noti.btn_cancel', '취소')}
              </button>
              <button
                className="modal-btn confirm"
                onClick={confirmUse}
                disabled={isProcessing}
              >
                {isProcessing ? '처리 중...' : t('coupon.staff_use_btn', '사용 처리')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 사용 처리 완료 모달 */}
      {doneModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-body">
              {t('coupon.staff_use_done', '쿠폰 사용 처리가 완료되었습니다.')}
            </div>
            <div className="modal-actions">
              <button
                className="modal-btn confirm"
                style={{ borderLeft: 'none' }}
                onClick={() => setDoneModalOpen(false)}
              >
                {t('noti.btn_confirm', '확인')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Coupons;
