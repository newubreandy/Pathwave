import React, { useState, useEffect } from 'react';
import { Wifi, Gift, Bell, X, AlertTriangle, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import BillingService from '../services/billing/BillingService';
import Button from '../components/common/Button';
import SectionTabs from '../components/common/SectionTabs';
import './PaymentManagement.css';

// 백엔드 service_type → 아이콘 매핑
const PLAN_ICONS = {
  wifi: Wifi,
  event: Gift,
  notification: Bell,
};

const STATUS_KEYS = {
  active: 'subscription.active',
  expired: 'subscription.expired',
  canceled: 'subscription.canceled',
};

const STATUS_CSS = {
  active: 'sub-badge--active',
  expired: 'sub-badge--expired',
  canceled: 'sub-badge--canceled',
};

/* ── 해지 확인 모달 ── */
const CancelModal = ({ sub, onClose, onConfirm }) => {
  const { t } = useTranslation();
  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" style={{ maxWidth: 400 }} onClick={e => e.stopPropagation()}>
        <div className="settings-modal-header">
          <h3 className="settings-modal-title">{t('subscription.cancel_btn')}</h3>
          <button className="settings-modal-close" onClick={onClose} aria-label="닫기">
            <X size={20} />
          </button>
        </div>
        <div className="settings-modal-body">
          <p style={{ fontSize: 'var(--pw-label-size)', color: 'var(--pw-text-secondary)', whiteSpace: 'pre-line', marginBottom: 'var(--pw-space-4)' }}>
            {t('subscription.cancel_confirm')}
          </p>
          <div className="sub-cancel-warning">
            <AlertTriangle size={14} aria-hidden="true" />
            <span>{t('subscription.cancel_warning')}</span>
          </div>
          <div className="settings-modal-actions" style={{ marginTop: 'var(--pw-space-5)' }}>
            <button className="settings-modal-btn cancel" onClick={onClose}>취소</button>
            <button className="settings-modal-btn confirm" onClick={() => onConfirm(sub.id)}>해지 확인</button>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ── 구독 카드 ── */
const SubscriptionCard = ({ sub, onCancel, onExtend }) => {
  const { t } = useTranslation();
  // 백엔드 필드: service_type, quantity, period_months, total_price, started_at, ends_at, status
  const Icon = PLAN_ICONS[sub.service_type] || Wifi;
  const isActive = sub.status === 'active';
  const periodLabel = sub.period_months === 12 ? '연간' : '월간';

  // ISO 날짜 → YYYY-MM-DD 표시
  const fmtDate = (iso) => {
    if (!iso) return '-';
    return String(iso).slice(0, 10);
  };

  return (
    <div className={`sub-card ${isActive ? '' : 'sub-card--inactive'}`}>
      <div className="sub-card-header">
        <div className="sub-card-icon">
          <Icon size={20} strokeWidth={2} />
        </div>
        <div className="sub-card-meta">
          <div className="sub-card-plan">
            {t(`subscription.plan_${sub.service_type}`, sub.service_type)} × {sub.quantity}
          </div>
          <div className="sub-card-period">{periodLabel}</div>
        </div>
        <span className={`sub-badge ${STATUS_CSS[sub.status] || ''}`}>
          {t(STATUS_KEYS[sub.status] || '', sub.status)}
        </span>
      </div>

      <div className="sub-card-dates">
        <div className="sub-card-date-row">
          <span className="sub-card-date-label">{t('subscription.start_at')}</span>
          <span className="sub-card-date-value">{fmtDate(sub.started_at)}</span>
        </div>
        <div className="sub-card-date-row">
          <span className="sub-card-date-label">{t('subscription.end_at')}</span>
          <span className="sub-card-date-value">{fmtDate(sub.ends_at)}</span>
        </div>
        <div className="sub-card-date-row">
          <span className="sub-card-date-label">{t('billing.total_label')}</span>
          <span className="sub-card-amount">{Number(sub.total_price).toLocaleString()}원</span>
        </div>
      </div>

      {isActive && (
        <div className="sub-card-footer">
          <p className="sub-renewal-notice">{t('subscription.renewal_notice')}</p>
          <div style={{ display: 'flex', gap: 'var(--pw-space-2)' }}>
            {onExtend && (
              <Button variant="outline" size="small" onClick={() => onExtend(sub)}>
                연장
              </Button>
            )}
            <Button variant="outline" size="small" onClick={() => onCancel(sub)}>
              {t('subscription.cancel_btn')}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

/* ══════════════════════════════════════════
   Main
   ══════════════════════════════════════════ */
const Subscriptions = () => {
  const { t } = useTranslation();
  const [filter, setFilter] = useState('active');
  const [subs, setSubs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState('');
  const [cancelTarget, setCancelTarget] = useState(null);
  const [extendTarget, setExtendTarget] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');

  const loadSubscriptions = async () => {
    setLoading(true);
    setFetchError('');
    try {
      const res = await BillingService.listSubscriptions();
      setSubs(res.subscriptions || []);
    } catch (err) {
      setFetchError(err.message || '구독 목록을 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubscriptions();
  }, []);

  const filtered = filter === 'all' ? subs : subs.filter(s => s.status === filter);

  const handleCancelConfirm = async (id) => {
    setActionLoading(true);
    setActionError('');
    try {
      await BillingService.cancelSubscription(id);
      await loadSubscriptions();
    } catch (err) {
      setActionError(err.message || '해지에 실패했습니다.');
    } finally {
      setActionLoading(false);
      setCancelTarget(null);
    }
  };

  const handleExtendConfirm = async (id) => {
    setActionLoading(true);
    setActionError('');
    try {
      await BillingService.extendSubscription(id);
      await loadSubscriptions();
    } catch (err) {
      setActionError(err.message || '연장에 실패했습니다.');
    } finally {
      setActionLoading(false);
      setExtendTarget(null);
    }
  };

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <h1 className="page-title">{t('subscription.title')}</h1>
        <p className="sub-title">이용 중인 서비스 구독을 확인하고 관리합니다.</p>
      </div>

      <SectionTabs
        tabs={[
          { key: 'active',   label: t('subscription.active') },
          { key: 'canceled', label: t('subscription.canceled') },
          { key: 'all',      label: '전체' },
        ]}
        value={filter}
        onChange={setFilter}
        ariaLabel="구독 상태 필터"
      />

      <div style={{ marginTop: 'var(--pw-space-8)' }}>
        {loading ? (
          <div className="sub-empty">
            <RefreshCw size={36} strokeWidth={1} />
            <p>불러오는 중...</p>
          </div>
        ) : fetchError ? (
          <div style={{ color: 'var(--pw-danger)', padding: 'var(--pw-space-4)', fontSize: 'var(--pw-label-size)' }}>
            {fetchError}
          </div>
        ) : filtered.length === 0 ? (
          <div className="sub-empty">
            <RefreshCw size={36} strokeWidth={1} />
            <p>{t('subscription.no_subscriptions')}</p>
          </div>
        ) : (
          <div className="sub-list">
            {filtered.map(sub => (
              <SubscriptionCard
                key={sub.id}
                sub={sub}
                onCancel={setCancelTarget}
                onExtend={setExtendTarget}
              />
            ))}
          </div>
        )}

        {actionError && (
          <div style={{ color: 'var(--pw-danger)', padding: 'var(--pw-space-3)', fontSize: 'var(--pw-label-size)' }}>
            {actionError}
          </div>
        )}

        {/* 하단 compliance 문구 */}
        <div className="sub-compliance-terms">
          <p>{t('subscription.compliance_terms')}</p>
        </div>
      </div>

      {cancelTarget && (
        <CancelModal
          sub={cancelTarget}
          onClose={() => setCancelTarget(null)}
          onConfirm={handleCancelConfirm}
        />
      )}

      {/* 연장 확인 모달 */}
      {extendTarget && (
        <div className="settings-modal-overlay" onClick={() => setExtendTarget(null)}>
          <div className="settings-modal" style={{ maxWidth: 400 }} onClick={e => e.stopPropagation()}>
            <div className="settings-modal-header">
              <h3 className="settings-modal-title">구독 연장</h3>
              <button className="settings-modal-close" onClick={() => setExtendTarget(null)} aria-label="닫기">
                <X size={20} />
              </button>
            </div>
            <div className="settings-modal-body">
              <p style={{ fontSize: 'var(--pw-label-size)', color: 'var(--pw-text-secondary)', marginBottom: 'var(--pw-space-4)' }}>
                현재 구독과 동일한 조건으로 연장합니다. 즉시 결제가 진행됩니다.
              </p>
              <div className="settings-modal-actions" style={{ marginTop: 'var(--pw-space-5)' }}>
                <button className="settings-modal-btn cancel" onClick={() => setExtendTarget(null)} disabled={actionLoading}>취소</button>
                <button className="settings-modal-btn confirm" onClick={() => handleExtendConfirm(extendTarget.id)} disabled={actionLoading}>
                  {actionLoading ? '처리 중...' : '연장 확인'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Subscriptions;
