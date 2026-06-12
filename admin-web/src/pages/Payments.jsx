import React, { useEffect, useState, useCallback } from 'react';
import {
  RefreshCw, Receipt, RotateCcw, CreditCard, Calendar, AlertTriangle,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Modal from '../components/Modal.jsx';
import { adminApi } from '../services/admin.js';
import './Beacons.css';

const PAYMENT_FILTERS = ['all', 'paid', 'pending', 'failed', 'refunded'];
const SUB_FILTERS     = ['all', 'active', 'expired', 'cancelled'];

export default function Payments() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('payments');

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">{t('billing.title')}</h1>
            <p className="sub-title">{t('billing.subtitle')}</p>
          </div>
        </div>

        <div className="tab-bar">
          <button
            className={`tab-btn ${tab === 'payments' ? 'active' : ''}`}
            onClick={() => setTab('payments')}
          >
            <Receipt size={16} />
            <span>{t('billing.tab_payments')}</span>
          </button>
          <button
            className={`tab-btn ${tab === 'subscriptions' ? 'active' : ''}`}
            onClick={() => setTab('subscriptions')}
          >
            <Calendar size={16} />
            <span>{t('billing.tab_subscriptions')}</span>
          </button>
        </div>
      </div>

      {tab === 'payments'     && <PaymentsTab />}
      {tab === 'subscriptions' && <SubscriptionsTab />}
    </div>
  );
}


// ── 결제 탭 ──────────────────────────────────────────────────────────────────
function PaymentsTab() {
  const { t } = useTranslation();

  const statusLabel = {
    paid:      t('billing.status_paid'),
    pending:   t('billing.status_pending'),
    failed:    t('billing.status_failed'),
    refunded:  t('billing.status_refunded'),
    cancelled: t('billing.status_cancelled'),
  };
  const statusTone = {
    paid: 'active', pending: 'neutral', failed: 'inactive',
    refunded: 'neutral', cancelled: 'neutral',
  };

  const [filter, setFilter]         = useState({ status: 'all', date_from: '', date_to: '' });
  const [list, setList]             = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState('');
  const [refundTarget, setRefundTarget] = useState(null);
  const [detailTarget, setDetailTarget] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    const params = {};
    if (filter.status !== 'all') params.status    = filter.status;
    if (filter.date_from)        params.date_from  = filter.date_from;
    if (filter.date_to)          params.date_to    = filter.date_to;
    adminApi.listPayments(params)
      .then((data) => setList(data.payments || []))
      .catch((err) => setError(err.message || t('billing.load_error')))
      .finally(() => setLoading(false));
  }, [filter.status, filter.date_from, filter.date_to, t]);

  useEffect(() => { reload(); }, [reload]);

  const totalPaid     = list.filter((p) => p.status === 'paid').reduce((s, p) => s + (p.total || 0), 0);
  const totalRefunded = list.filter((p) => p.status === 'refunded').reduce((s, p) => s + (p.total || 0), 0);

  return (
    <>
      {/* 부가세 안내 */}
      <div className="card" style={{
        display: 'flex', gap: 12, alignItems: 'flex-start',
        background: 'var(--bg-3)', border: '1px solid var(--border)',
        padding: '0.875rem 1.25rem',
      }}>
        <AlertTriangle size={16} style={{ color: 'var(--accent)', flexShrink: 0, marginTop: 2 }} />
        <p style={{ margin: 0, fontSize: 'var(--fs-sm)', color: 'var(--text-muted)' }}>
          {t('billing.compliance_warning')}
        </p>
      </div>

      <div className="filter-bar">
        <div className="filter-group">
          <span className="filter-label">{t('billing.filter_status')}</span>
          <select
            value={filter.status}
            onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}
          >
            {PAYMENT_FILTERS.map((s) => (
              <option key={s} value={s}>
                {s === 'all' ? t('billing.filter_all') : (statusLabel[s] || s)}
              </option>
            ))}
          </select>
        </div>
        <div className="filter-group">
          <span className="filter-label">{t('billing.filter_period')}</span>
          <input
            type="date"
            value={filter.date_from}
            onChange={(e) => setFilter((f) => ({ ...f, date_from: e.target.value }))}
          />
          <span className="text-hint">~</span>
          <input
            type="date"
            value={filter.date_to}
            onChange={(e) => setFilter((f) => ({ ...f, date_to: e.target.value }))}
          />
        </div>
        <button className="btn btn-ghost" onClick={reload} disabled={loading} aria-label="새로고침">
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
        </button>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-icon accent">
            <Receipt size={20} strokeWidth={1.75} />
          </div>
          <div className="stat-content">
            <div className="stat-label">{t('billing.stat_paid_total')}</div>
            <div className="stat-value">{totalPaid.toLocaleString()} 원</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">
            <RotateCcw size={20} strokeWidth={1.75} />
          </div>
          <div className="stat-content">
            <div className="stat-label">{t('billing.stat_refund_total')}</div>
            <div className="stat-value">{totalRefunded.toLocaleString()} 원</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">
            <CreditCard size={20} strokeWidth={1.75} />
          </div>
          <div className="stat-content">
            <div className="stat-label">{t('billing.stat_count')}</div>
            <div className="stat-value">{list.length}</div>
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>{error}</div>
      )}

      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>{t('billing.col_id')}</th>
              <th>{t('billing.col_order_no')}</th>
              <th>{t('billing.col_facility')}</th>
              <th>{t('billing.col_amount')}</th>
              <th>{t('billing.col_vat')}</th>
              <th>{t('billing.col_total')}</th>
              <th>{t('billing.col_pg_tid')}</th>
              <th>{t('billing.col_status')}</th>
              <th>{t('billing.col_paid_at')}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={10} className="row-empty">{t('billing.loading')}</td></tr>}
            {!loading && list.length === 0 && (
              <tr><td colSpan={10} className="row-empty">{t('billing.empty')}</td></tr>
            )}
            {!loading && list.map((p) => {
              const tone = statusTone[p.status] || 'neutral';
              const label = statusLabel[p.status] || p.status;
              return (
                <tr key={p.id} className="row-clickable" onClick={() => setDetailTarget(p)}>
                  <td className="cell-mono">{p.id}</td>
                  <td className="cell-mono">{p.order_no || '—'}</td>
                  <td className="cell-mono">{p.facility_account_id ?? '—'}</td>
                  <td className="cell-mono">{p.amount?.toLocaleString() ?? '—'}</td>
                  <td className="cell-mono">{p.vat?.toLocaleString() ?? '—'}</td>
                  <td className="cell-mono"><strong>{p.total?.toLocaleString() ?? '—'}</strong></td>
                  <td className="cell-mono cell-uuid" title={p.pg_tid}>{p.pg_tid || '—'}</td>
                  <td>
                    <span className={`status-badge ${tone}`}>{label}</span>
                  </td>
                  <td className="cell-mono">{(p.paid_at || p.created_at)?.slice(0, 16) || '—'}</td>
                  <td className="cell-actions">
                    {p.status === 'paid' && (
                      <button
                        className="icon-btn"
                        title={t('billing.refund_btn_confirm')}
                        onClick={(e) => { e.stopPropagation(); setRefundTarget(p); }}
                      >
                        <RotateCcw size={15} />
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <RefundModal
        payment={refundTarget}
        onClose={() => setRefundTarget(null)}
        onRefunded={() => { setRefundTarget(null); reload(); }}
      />
      <PaymentDetailModal
        payment={detailTarget}
        statusLabel={statusLabel}
        statusTone={statusTone}
        onClose={() => setDetailTarget(null)}
        onRefund={(p) => { setDetailTarget(null); setRefundTarget(p); }}
      />
    </>
  );
}


// ── 구독 탭 ──────────────────────────────────────────────────────────────────
function SubscriptionsTab() {
  const { t } = useTranslation();

  const statusLabel = {
    active:    t('subscription.status_active'),
    expired:   t('subscription.status_expired'),
    cancelled: t('subscription.status_cancelled'),
  };
  const statusTone = { active: 'active', expired: 'neutral', cancelled: 'inactive' };

  const [filter, setFilter]      = useState({ status: 'all' });
  const [list, setList]          = useState([]);
  const [loading, setLoading]    = useState(true);
  const [error, setError]        = useState('');
  const [detailTarget, setDetailTarget] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    const params = {};
    if (filter.status !== 'all') params.status = filter.status;
    adminApi.listSubscriptions(params)
      .then((data) => setList(data.subscriptions || []))
      .catch((err) => setError(err.message || t('subscription.load_error')))
      .finally(() => setLoading(false));
  }, [filter.status, t]);

  useEffect(() => { reload(); }, [reload]);

  return (
    <>
      <div className="filter-bar">
        <div className="filter-group">
          <span className="filter-label">{t('subscription.filter_status')}</span>
          <select
            value={filter.status}
            onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}
          >
            {SUB_FILTERS.map((s) => (
              <option key={s} value={s}>
                {s === 'all' ? t('subscription.filter_all') : (statusLabel[s] || s)}
              </option>
            ))}
          </select>
        </div>
        <button className="btn btn-ghost" onClick={reload} disabled={loading} aria-label="새로고침">
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
        </button>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>{error}</div>
      )}

      <SubDetailModal
        sub={detailTarget}
        statusLabel={statusLabel}
        statusTone={statusTone}
        onClose={() => setDetailTarget(null)}
      />

      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>{t('subscription.col_id')}</th>
              <th>{t('subscription.col_facility')}</th>
              <th>{t('subscription.col_service')}</th>
              <th>{t('subscription.col_qty')}</th>
              <th>{t('subscription.col_period')}</th>
              <th>{t('subscription.col_unit_price')}</th>
              <th>{t('subscription.col_total')}</th>
              <th>{t('subscription.col_started_at')}</th>
              <th>{t('subscription.col_ends_at')}</th>
              <th>{t('subscription.col_status')}</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={10} className="row-empty">{t('subscription.loading')}</td></tr>}
            {!loading && list.length === 0 && (
              <tr><td colSpan={10} className="row-empty">{t('subscription.empty')}</td></tr>
            )}
            {!loading && list.map((s) => {
              const tone  = statusTone[s.status]  || 'neutral';
              const label = statusLabel[s.status] || s.status;
              return (
                <tr key={s.id} className="row-clickable" onClick={() => setDetailTarget(s)}>
                  <td className="cell-mono">{s.id}</td>
                  <td className="cell-mono">{s.facility_account_id ?? '—'}</td>
                  <td>{s.service_type || '—'}</td>
                  <td className="cell-mono">{s.quantity ?? '—'}</td>
                  <td className="cell-mono">{s.period_months ?? '—'}</td>
                  <td className="cell-mono">{s.unit_price?.toLocaleString() ?? '—'}</td>
                  <td className="cell-mono"><strong>{s.total_price?.toLocaleString() ?? '—'}</strong></td>
                  <td className="cell-mono">{s.started_at?.slice(0, 10) || '—'}</td>
                  <td className="cell-mono">{s.ends_at?.slice(0, 10) || '—'}</td>
                  <td>
                    <span className={`status-badge ${tone}`}>{label}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}


// ── 환불 모달 ────────────────────────────────────────────────────────────────
function RefundModal({ payment, onClose, onRefunded }) {
  const { t } = useTranslation();
  const [reason, setReason] = useState('');
  const [busy, setBusy]     = useState(false);
  const [error, setError]   = useState('');

  useEffect(() => { if (payment) { setReason(''); setError(''); } }, [payment]);

  async function handleRefund() {
    setBusy(true); setError('');
    try {
      await adminApi.refundPayment(payment.id, { reason: reason.trim() || undefined });
      onRefunded?.();
    } catch (err) {
      setError(err.message || t('billing.refund_error'));
    } finally { setBusy(false); }
  }

  return (
    <Modal
      open={!!payment}
      onClose={onClose}
      title={payment ? t('billing.refund_title', { id: payment.id }) : ''}
      size="md"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>
            {t('billing.refund_btn_cancel')}
          </button>
          <button className="btn btn-danger" onClick={handleRefund} disabled={busy}>
            {busy ? t('billing.refund_btn_busy') : t('billing.refund_btn_confirm')}
          </button>
        </>
      }
    >
      {payment && (
        <>
          <div className="kv">
            <div><span className="kv-key">{t('billing.refund_order_no')}</span> <span className="cell-mono">{payment.order_no}</span></div>
            <div><span className="kv-key">{t('billing.refund_facility')}</span> {payment.facility_account_id}</div>
            <div><span className="kv-key">{t('billing.refund_amount')}</span> {payment.amount?.toLocaleString()} 원</div>
            <div><span className="kv-key">{t('billing.refund_vat')}</span> {payment.vat?.toLocaleString()} 원</div>
            <div><span className="kv-key">{t('billing.refund_total')}</span> <strong>{payment.total?.toLocaleString()} 원</strong></div>
            <div><span className="kv-key">{t('billing.refund_pg_tid')}</span> <span className="cell-mono">{payment.pg_tid}</span></div>
            <div><span className="kv-key">{t('billing.refund_paid_at')}</span> {payment.paid_at}</div>
          </div>
          <p className="text-muted" style={{ marginTop: '1rem', fontSize: '0.875rem' }}>
            {t('billing.refund_sim_warning')}
          </p>
          <label className="form-label">
            <span>{t('billing.refund_reason_label')}</span>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={t('billing.refund_reason_placeholder')}
              disabled={busy}
            />
          </label>
          {error && <div className="error-box">{error}</div>}
        </>
      )}
    </Modal>
  );
}


// ── 결제 상세 모달 (읽기 전용) ────────────────────────────────────────────────
function PaymentDetailModal({ payment: p, statusLabel, statusTone, onClose, onRefund }) {
  const { t } = useTranslation();
  if (!p) return null;
  const tone  = statusTone[p.status]  || 'neutral';
  const label = statusLabel[p.status] || p.status;
  return (
    <Modal
      open={!!p}
      onClose={onClose}
      title={`결제 상세 — #${p.id}`}
      size="md"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose}>{t('common.close') || '닫기'}</button>
          {p.status === 'paid' && (
            <button className="btn btn-danger" onClick={() => onRefund(p)}>
              <RotateCcw size={15} style={{ marginRight: 6 }} />
              {t('billing.refund_btn_confirm')}
            </button>
          )}
        </>
      }
    >
      <div className="kv">
        <div><span className="kv-key">{t('billing.col_id')}</span> <span className="cell-mono">{p.id}</span></div>
        <div><span className="kv-key">{t('billing.col_order_no')}</span> <span className="cell-mono">{p.order_no || '—'}</span></div>
        <div><span className="kv-key">{t('billing.col_facility')}</span> {p.facility_account_id ?? '—'}</div>
        <div><span className="kv-key">{t('billing.col_amount')}</span> {p.amount?.toLocaleString() ?? '—'} 원</div>
        <div><span className="kv-key">{t('billing.col_vat')}</span> {p.vat?.toLocaleString() ?? '—'} 원</div>
        <div><span className="kv-key">{t('billing.col_total')}</span> <strong>{p.total?.toLocaleString() ?? '—'} 원</strong></div>
        <div><span className="kv-key">{t('billing.col_pg_tid')}</span> <span className="cell-mono">{p.pg_tid || '—'}</span></div>
        <div>
          <span className="kv-key">{t('billing.col_status')}</span>
          {' '}<span className={`status-badge ${tone}`}>{label}</span>
        </div>
        <div><span className="kv-key">{t('billing.col_paid_at')}</span> {(p.paid_at || p.created_at) || '—'}</div>
      </div>
    </Modal>
  );
}


// ── 구독 상세 모달 (읽기 전용) ────────────────────────────────────────────────
function SubDetailModal({ sub: s, statusLabel, statusTone, onClose }) {
  const { t } = useTranslation();
  if (!s) return null;
  const tone  = statusTone[s.status]  || 'neutral';
  const label = statusLabel[s.status] || s.status;
  return (
    <Modal
      open={!!s}
      onClose={onClose}
      title={`구독 상세 — #${s.id}`}
      size="md"
      footer={
        <button className="btn btn-ghost" onClick={onClose}>{t('common.close') || '닫기'}</button>
      }
    >
      <div className="kv">
        <div><span className="kv-key">{t('subscription.col_id')}</span> <span className="cell-mono">{s.id}</span></div>
        <div><span className="kv-key">{t('subscription.col_facility')}</span> {s.facility_account_id ?? '—'}</div>
        <div><span className="kv-key">{t('subscription.col_service')}</span> {s.service_type || '—'}</div>
        <div><span className="kv-key">{t('subscription.col_qty')}</span> {s.quantity ?? '—'}</div>
        <div><span className="kv-key">{t('subscription.col_period')}</span> {s.period_months ?? '—'} 개월</div>
        <div><span className="kv-key">{t('subscription.col_unit_price')}</span> {s.unit_price?.toLocaleString() ?? '—'} 원</div>
        <div><span className="kv-key">{t('subscription.col_total')}</span> <strong>{s.total_price?.toLocaleString() ?? '—'} 원</strong></div>
        <div><span className="kv-key">{t('subscription.col_started_at')}</span> {s.started_at?.slice(0, 10) || '—'}</div>
        <div><span className="kv-key">{t('subscription.col_ends_at')}</span> {s.ends_at?.slice(0, 10) || '—'}</div>
        <div>
          <span className="kv-key">{t('subscription.col_status')}</span>
          {' '}<span className={`status-badge ${tone}`}>{label}</span>
        </div>
      </div>
    </Modal>
  );
}
