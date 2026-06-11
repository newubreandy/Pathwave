import React, { useState, useEffect } from 'react';
import { Wifi, Gift, Bell, AlertTriangle, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Button from '../components/common/Button';
import SectionTabs from '../components/common/SectionTabs';
import PwModal from '../components/common/PwModal.jsx';
import './PaymentManagement.css';

/* ── Mock data — 실서비스에선 GET /api/billing/subscriptions 응답으로 대체 ── */
const MOCK_SUBSCRIPTIONS = [
  {
    id: 'sub-1',
    plan: 'wifi',
    period: 'monthly',
    status: 'active',
    startAt: '2026-03-12',
    endAt: '2026-06-12',
    amount: 1016000,
  },
  {
    id: 'sub-2',
    plan: 'notification',
    period: 'monthly',
    status: 'active',
    startAt: '2026-04-01',
    endAt: '2026-07-01',
    amount: 8100,
  },
  {
    id: 'sub-3',
    plan: 'event',
    period: 'yearly',
    status: 'canceled',
    startAt: '2025-01-01',
    endAt: '2026-01-01',
    amount: 72000,
  },
];

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
    <PwModal
      open
      onClose={onClose}
      title={t('subscription.cancel_btn')}
      size="sm"
      footer={
        <>
          <button className="settings-modal-btn cancel" onClick={onClose}>취소</button>
          <button className="settings-modal-btn confirm" onClick={() => onConfirm(sub.id)}>해지 확인</button>
        </>
      }
    >
      <p style={{ fontSize: 'var(--pw-label-size)', color: 'var(--pw-text-secondary)', whiteSpace: 'pre-line', marginBottom: 'var(--pw-space-4)' }}>
        {t('subscription.cancel_confirm')}
      </p>
      <div className="sub-cancel-warning">
        <AlertTriangle size={14} aria-hidden="true" />
        <span>{t('subscription.cancel_warning')}</span>
      </div>
    </PwModal>
  );
};

/* ── 구독 카드 ── */
const SubscriptionCard = ({ sub, onCancel }) => {
  const { t } = useTranslation();
  const Icon = PLAN_ICONS[sub.plan] || Wifi;
  const isActive = sub.status === 'active';

  return (
    <div className={`sub-card ${isActive ? '' : 'sub-card--inactive'}`}>
      <div className="sub-card-header">
        <div className="sub-card-icon">
          <Icon size={20} strokeWidth={2} />
        </div>
        <div className="sub-card-meta">
          <div className="sub-card-plan">{t(`subscription.plan_${sub.plan}`)}</div>
          <div className="sub-card-period">{t(`subscription.period_${sub.period}`)}</div>
        </div>
        <span className={`sub-badge ${STATUS_CSS[sub.status]}`}>
          {t(STATUS_KEYS[sub.status])}
        </span>
      </div>

      <div className="sub-card-dates">
        <div className="sub-card-date-row">
          <span className="sub-card-date-label">{t('subscription.start_at')}</span>
          <span className="sub-card-date-value">{sub.startAt}</span>
        </div>
        <div className="sub-card-date-row">
          <span className="sub-card-date-label">{t('subscription.end_at')}</span>
          <span className="sub-card-date-value">{sub.endAt}</span>
        </div>
        <div className="sub-card-date-row">
          <span className="sub-card-date-label">{t('billing.total_label')}</span>
          <span className="sub-card-amount">{sub.amount.toLocaleString()}원</span>
        </div>
      </div>

      {isActive && (
        <div className="sub-card-footer">
          <p className="sub-renewal-notice">{t('subscription.renewal_notice')}</p>
          <Button variant="outline" size="small" onClick={() => onCancel(sub)}>
            {t('subscription.cancel_btn')}
          </Button>
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
  const [cancelTarget, setCancelTarget] = useState(null);

  useEffect(() => {
    // 실서비스: GET /api/billing/subscriptions
    setSubs(MOCK_SUBSCRIPTIONS);
  }, []);

  const filtered = filter === 'all' ? subs : subs.filter(s => s.status === filter);

  const handleCancelConfirm = async (id) => {
    // 실서비스: POST /api/billing/subscriptions/{id}/cancel
    setSubs(prev => prev.map(s => s.id === id ? { ...s, status: 'canceled' } : s));
    setCancelTarget(null);
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
        {filtered.length === 0 ? (
          <div className="sub-empty">
            <RefreshCw size={36} strokeWidth={1} />
            <p>{t('subscription.no_subscriptions')}</p>
          </div>
        ) : (
          <div className="sub-list">
            {filtered.map(sub => (
              <SubscriptionCard key={sub.id} sub={sub} onCancel={setCancelTarget} />
            ))}
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
    </div>
  );
};

export default Subscriptions;
