import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Ticket, Plus, ChevronRight, Info } from 'lucide-react';
import BottomActionBar from '../components/common/BottomActionBar';
import Button from '../components/common/Button';
import { useDialog } from '../components/common/DialogProvider';
import StoreService from '../services/store/StoreService';
import CouponService from '../services/coupon/CouponService';
import '../pages/Stamps.css'; // 쿠폰/스탬프 리스트는 동일 카드 스타일 공유
import './Notifications.css'; // modal-overlay / modal-content / modal-btn 공통 스타일

const Coupons = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { alert: dialogAlert } = useDialog();

  // 1계정 1매장 — 마운트 시 fid 확보 후 쿠폰 목록 로드
  const [fid, setFid] = useState(null);
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errMsg, setErrMsg] = useState('');

  // 사용 처리 모달
  const [useModalCouponId, setUseModalCouponId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [doneModalOpen, setDoneModalOpen] = useState(false);

  const loadCoupons = useCallback(async (facilityId) => {
    try {
      const r = await CouponService.list(facilityId);
      setCoupons(r.coupons ?? []);
    } catch (err) {
      setErrMsg(err?.message || '쿠폰을 불러오지 못했습니다.');
    }
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await StoreService.list();
        const f = (res.facilities ?? [])[0];
        if (!alive) return;
        if (!f) { setErrMsg('등록된 매장이 없습니다.'); return; }
        setFid(f.id);
        await loadCoupons(f.id);
      } catch (err) {
        if (alive) setErrMsg(err?.message || '매장 정보를 불러오지 못했습니다.');
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [loadCoupons]);

  const openUseModal = (e, id) => {
    e.preventDefault(); // Link 탐색 방지
    e.stopPropagation();
    setUseModalCouponId(id);
  };

  const confirmUse = async () => {
    if (!useModalCouponId) return;
    setIsProcessing(true);
    try {
      await CouponService.use(useModalCouponId);
      setUseModalCouponId(null);
      setDoneModalOpen(true);
      if (fid) await loadCoupons(fid); // 목록 갱신 — 사용 완료 상태 반영
    } catch (err) {
      setUseModalCouponId(null);
      await dialogAlert({
        title: t('coupon.staff_use_failed_title', '쿠폰 사용 실패'),
        message: err?.message || t('coupon.staff_use_failed', '쿠폰 사용에 실패했습니다. 잠시 후 다시 시도해 주세요.'),
      });
    } finally {
      setIsProcessing(false);
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
        <p className="sub-title">매장에서 발급한 쿠폰을 관리합니다.</p>
      </div>

      {errMsg && (
        <div style={{
          margin: 'var(--pw-space-4)',
          padding: 'var(--pw-space-3) var(--pw-space-4)',
          border: '1px solid var(--pw-error)',
          color: 'var(--pw-error)',
          borderRadius: 'var(--pw-radius-sm)',
          fontSize: 'var(--pw-caption-size)',
        }}>{errMsg}</div>
      )}

      <div className="stamp-list">
        {loading ? (
          <div className="empty-state"><p>로딩 중...</p></div>
        ) : coupons.length === 0 ? (
          <div className="empty-state"><p>등록된 쿠폰이 없습니다.</p></div>
        ) : (
          coupons.map((coupon) => {
            const expiresAt = coupon.expires_at?.slice(0, 10);
            return (
              <Link to={`/dashboard/coupons/view/${coupon.id}`} key={coupon.id} className="stamp-card">
                <div className={`stamp-icon ${coupon.status}`}>
                  <Ticket size={24} />
                </div>
                <div className="stamp-info">
                  <div className="stamp-info-head">
                    <h3 className="stamp-name" style={coupon.status === 'used' ? { color: 'var(--pw-text-hint)' } : {}}>
                      {coupon.title || t('coupon.default_title', '쿠폰')}
                    </h3>
                    <span className={`stamp-status ${coupon.status}`}>
                      {statusLabel(coupon.status)}
                    </span>
                  </div>
                  <div className="stamp-details">
                    <div>
                      {coupon.benefit || ''}
                      {expiresAt ? ` · ${t('coupon.expires_label', '만료')} ${expiresAt}` : ''}
                    </div>
                  </div>
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
            );
          })
        )}
      </div>

      <BottomActionBar>
        <Button
          variant="primary"
          fullWidth
          icon={<Plus size={18} />}
          onClick={() => navigate('/dashboard/coupons/new')}
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
