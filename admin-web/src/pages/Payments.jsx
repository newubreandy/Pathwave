import React, { useEffect, useState, useCallback } from 'react';
import {
  RefreshCw, Search, Receipt, RotateCcw, CreditCard, Calendar,
} from 'lucide-react';
import Modal from '../components/Modal.jsx';
import { adminApi } from '../services/admin.js';
import './Beacons.css';
import './Payments.css';

const PAYMENT_STATUS = {
  paid:     { label: '결제 완료',  color: '#2ea043' },
  pending:  { label: '대기',      color: '#d29922' },
  failed:   { label: '실패',      color: '#da3633' },
  refunded: { label: '환불됨',    color: '#a371f7' },
  cancelled:{ label: '취소',      color: '#8b949e' },
};
const SUBSCRIPTION_STATUS = {
  active:    { label: '구독 중',  color: '#2ea043' },
  expired:   { label: '만료',     color: '#8b949e' },
  cancelled: { label: '해지',     color: '#da3633' },
};

const PAYMENT_FILTERS = ['all', 'paid', 'pending', 'failed', 'refunded'];
const SUB_FILTERS = ['all', 'active', 'expired', 'cancelled'];

export default function Payments() {
  const [tab, setTab] = useState('payments');

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">결제 · 구독</h1>
            <p className="sub-title">전체 결제 내역 / 환불 처리 / 구독 현황.</p>
          </div>
        </div>

        <div className="tab-bar">
          <button
            className={`tab-btn ${tab === 'payments' ? 'active' : ''}`}
            onClick={() => setTab('payments')}
          >
            <Receipt size={16} />
            <span>결제 내역</span>
          </button>
          <button
            className={`tab-btn ${tab === 'subscriptions' ? 'active' : ''}`}
            onClick={() => setTab('subscriptions')}
          >
            <Calendar size={16} />
            <span>구독</span>
          </button>
        </div>
      </div>

      {tab === 'payments' && <PaymentsTab />}
      {tab === 'subscriptions' && <SubscriptionsTab />}
    </div>
  );
}


// ── 결제 탭 ──────────────────────────────────────────────────────────────────
function PaymentsTab() {
  const [filter, setFilter] = useState({ status: 'all', date_from: '', date_to: '' });
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refundTarget, setRefundTarget] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    const params = {};
    if (filter.status !== 'all') params.status = filter.status;
    if (filter.date_from) params.date_from = filter.date_from;
    if (filter.date_to)   params.date_to = filter.date_to;
    adminApi.listPayments(params)
      .then((data) => setList(data.payments || []))
      .catch((err) => setError(err.message || '결제 내역을 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [filter.status, filter.date_from, filter.date_to]);

  useEffect(() => { reload(); }, [reload]);

  const totalPaid = list.filter((p) => p.status === 'paid').reduce((s, p) => s + (p.total || 0), 0);
  const totalRefunded = list.filter((p) => p.status === 'refunded').reduce((s, p) => s + (p.total || 0), 0);

  return (
    <>
      <div className="filter-bar">
        <div className="filter-group">
          <span className="filter-label">상태</span>
          <select value={filter.status} onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}>
            {PAYMENT_FILTERS.map((s) => (
              <option key={s} value={s}>{s === 'all' ? '전체' : PAYMENT_STATUS[s]?.label || s}</option>
            ))}
          </select>
        </div>
        <div className="filter-group">
          <span className="filter-label">기간</span>
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
        <button className="btn btn-ghost" onClick={reload} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
        </button>
      </div>

      <div className="stat-grid" style={{ marginBottom: '1rem' }}>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#2ea04322', color: '#2ea043' }}>
            <Receipt size={20} />
          </div>
          <div className="stat-content">
            <div className="stat-label">결제 합계 (필터)</div>
            <div className="stat-value">{totalPaid.toLocaleString()} 원</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#a371f722', color: '#a371f7' }}>
            <RotateCcw size={20} />
          </div>
          <div className="stat-content">
            <div className="stat-label">환불 합계</div>
            <div className="stat-value">{totalRefunded.toLocaleString()} 원</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#1f6feb22', color: '#1f6feb' }}>
            <CreditCard size={20} />
          </div>
          <div className="stat-content">
            <div className="stat-label">건수</div>
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
              <th>ID</th>
              <th>주문번호</th>
              <th>사장 #</th>
              <th>금액</th>
              <th>VAT</th>
              <th>합계</th>
              <th>PG TID</th>
              <th>상태</th>
              <th>결제일</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={10} className="row-empty">로딩 중...</td></tr>}
            {!loading && list.length === 0 && (
              <tr><td colSpan={10} className="row-empty">결제 내역이 없습니다.</td></tr>
            )}
            {!loading && list.map((p) => {
              const st = PAYMENT_STATUS[p.status] || { label: p.status, color: '#8b949e' };
              return (
                <tr key={p.id}>
                  <td className="cell-mono">{p.id}</td>
                  <td className="cell-mono">{p.order_no || '—'}</td>
                  <td className="cell-mono">{p.facility_account_id ?? '—'}</td>
                  <td className="cell-mono">{p.amount?.toLocaleString() ?? '—'}</td>
                  <td className="cell-mono">{p.vat?.toLocaleString() ?? '—'}</td>
                  <td className="cell-mono"><strong>{p.total?.toLocaleString() ?? '—'}</strong></td>
                  <td className="cell-mono cell-uuid" title={p.pg_tid}>{p.pg_tid || '—'}</td>
                  <td>
                    <span className="status-pill" style={{ background: st.color + '22', color: st.color }}>
                      {st.label}
                    </span>
                  </td>
                  <td className="cell-mono">{(p.paid_at || p.created_at)?.slice(0, 16) || '—'}</td>
                  <td className="cell-actions">
                    {p.status === 'paid' && (
                      <button
                        className="icon-btn"
                        title="환불"
                        onClick={() => setRefundTarget(p)}
                        style={{ color: '#a371f7' }}
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
    </>
  );
}


// ── 구독 탭 ──────────────────────────────────────────────────────────────────
function SubscriptionsTab() {
  const [filter, setFilter] = useState({ status: 'all' });
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const reload = useCallback(() => {
    setLoading(true); setError('');
    const params = {};
    if (filter.status !== 'all') params.status = filter.status;
    adminApi.listSubscriptions(params)
      .then((data) => setList(data.subscriptions || []))
      .catch((err) => setError(err.message || '구독 목록을 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [filter.status]);

  useEffect(() => { reload(); }, [reload]);

  return (
    <>
      <div className="filter-bar">
        <div className="filter-group">
          <span className="filter-label">상태</span>
          <select value={filter.status} onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}>
            {SUB_FILTERS.map((s) => (
              <option key={s} value={s}>{s === 'all' ? '전체' : SUBSCRIPTION_STATUS[s]?.label || s}</option>
            ))}
          </select>
        </div>
        <button className="btn btn-ghost" onClick={reload} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
        </button>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>{error}</div>
      )}

      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>사장 #</th>
              <th>서비스</th>
              <th>수량</th>
              <th>기간(개월)</th>
              <th>단가</th>
              <th>합계</th>
              <th>시작</th>
              <th>종료</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={10} className="row-empty">로딩 중...</td></tr>}
            {!loading && list.length === 0 && (
              <tr><td colSpan={10} className="row-empty">구독 내역이 없습니다.</td></tr>
            )}
            {!loading && list.map((s) => {
              const st = SUBSCRIPTION_STATUS[s.status] || { label: s.status, color: '#8b949e' };
              return (
                <tr key={s.id}>
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
                    <span className="status-pill" style={{ background: st.color + '22', color: st.color }}>
                      {st.label}
                    </span>
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
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { if (payment) { setReason(''); setError(''); } }, [payment]);

  async function handleRefund() {
    setBusy(true); setError('');
    try {
      await adminApi.refundPayment(payment.id, { reason: reason.trim() || undefined });
      onRefunded?.();
    } catch (err) {
      setError(err.message || '환불에 실패했습니다.');
    } finally { setBusy(false); }
  }

  return (
    <Modal
      open={!!payment}
      onClose={onClose}
      title={payment ? `결제 환불 — #${payment.id}` : ''}
      size="md"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-danger" onClick={handleRefund} disabled={busy}>
            {busy ? '처리 중...' : '환불 확정'}
          </button>
        </>
      }
    >
      {payment && (
        <>
          <div className="kv">
            <div><span className="kv-key">주문번호</span> <span className="cell-mono">{payment.order_no}</span></div>
            <div><span className="kv-key">사장 ID</span> {payment.facility_account_id}</div>
            <div><span className="kv-key">금액</span> {payment.amount?.toLocaleString()} 원</div>
            <div><span className="kv-key">VAT</span> {payment.vat?.toLocaleString()} 원</div>
            <div><span className="kv-key">합계</span> <strong>{payment.total?.toLocaleString()} 원</strong></div>
            <div><span className="kv-key">PG TID</span> <span className="cell-mono">{payment.pg_tid}</span></div>
            <div><span className="kv-key">결제일</span> {payment.paid_at}</div>
          </div>
          <p className="text-muted" style={{ marginTop: '1rem', fontSize: '0.875rem' }}>
            ⚠️ 현재는 시뮬 모드 — 실 PG 연동 후 토스/이니시스 환불 API 호출됩니다.
          </p>
          <label className="form-label">
            <span>환불 사유 (선택)</span>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="예: 사용자 요청 / 잘못된 결제"
              disabled={busy}
            />
          </label>
          {error && <div className="error-box">{error}</div>}
        </>
      )}
    </Modal>
  );
}
