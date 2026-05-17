import React, { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { RefreshCw, MessageSquare, CheckCircle2, AlertCircle, Send } from 'lucide-react';
import Modal from '../components/Modal.jsx';
import { adminApi } from '../services/admin.js';

const KIND_TABS = ['user', 'provider'];
const STATUS_FILTERS = ['', 'open', 'replied', 'closed'];

export default function Support() {
  const { t } = useTranslation();

  const [kind, setKind] = useState('user');
  const [status, setStatus] = useState('');
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeId, setActiveId] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    const params = { kind };
    if (status) params.status = status;
    adminApi.listSupportTickets(params)
      .then((d) => setList(d.tickets || []))
      .catch((e) => setError(e.message || '문의를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [kind, status]);

  useEffect(() => { reload(); }, [reload]);

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">{t('admin_support.inbox_title', '문의 inbox')}</h1>
            <p className="sub-title">
              {t('support.business_hours', '운영시간: 평일 09:00~18:00 (주말/공휴일 휴무)')} ·
              {' '}{t('support.response_time', '응답 예상 시간: 영업일 1~3일 이내')}
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>{t('notif.btn_refresh', '새로고침')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 탭 (사용자/사장님) */}
      <div className="card" style={{ display: 'flex', gap: 8, padding: 12, marginBottom: 12 }}>
        {KIND_TABS.map((k) => (
          <button
            key={k}
            onClick={() => setKind(k)}
            className={`btn ${kind === k ? 'btn-primary' : 'btn-ghost'}`}
          >
            {k === 'user'
              ? t('admin_support.tab_user', '사용자')
              : t('admin_support.tab_provider', '사장님')}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="form-input">
          {STATUS_FILTERS.map((s) => (
            <option key={s} value={s}>
              {s === '' ? t('admin_support.filter_all', '전체')
                : s === 'open' ? t('admin_support.filter_open', '답변 대기')
                : s === 'replied' ? t('admin_support.filter_replied', '답변 완료')
                : t('admin_support.filter_closed', '종결')}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>{t('admin_support.col_subject', '제목')}</th>
              <th>{t('admin_support.col_category', '카테고리')}</th>
              <th>{t('admin_support.col_priority', '우선순위')}</th>
              <th>{t('admin_support.col_status', '상태')}</th>
              <th>{t('admin_support.col_created', '접수일')}</th>
              <th>{t('admin_support.col_actions', '관리')}</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={7} className="row-empty">{t('common.loading', '불러오는 중...')}</td></tr>
            )}
            {!loading && list.length === 0 && (
              <tr><td colSpan={7} className="row-empty">접수된 문의가 없습니다.</td></tr>
            )}
            {!loading && list.map((it) => (
              <tr key={it.id}>
                <td className="cell-mono">{it.id}</td>
                <td>
                  <div style={{ fontWeight: 500 }}>{it.subject}</div>
                  <div className="text-hint" style={{ fontSize: 'var(--fs-xs)', marginTop: 2 }}>
                    {(it.body || '').slice(0, 60)}{(it.body || '').length > 60 ? '...' : ''}
                  </div>
                </td>
                <td>{it.category}</td>
                <td>
                  <PriorityBadge priority={it.priority} />
                </td>
                <td>
                  <StatusBadge status={it.status} />
                </td>
                <td className="cell-mono" style={{ fontSize: '0.8125rem' }}>
                  {(it.created_at || '').slice(0, 16)}
                </td>
                <td>
                  <button className="btn btn-ghost" onClick={() => setActiveId(it.id)}>
                    <MessageSquare size={14} />
                    <span>상세</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <TicketDetailModal
        ticketId={activeId}
        onClose={() => setActiveId(null)}
        onChanged={() => { setActiveId(null); reload(); }}
      />
    </div>
  );
}

function StatusBadge({ status }) {
  const map = {
    open:    { label: '답변 대기', color: '#facc15', bg: 'rgba(250,204,21,0.15)' },
    replied: { label: '답변 완료', color: '#22c55e', bg: 'rgba(34,197,94,0.15)' },
    closed:  { label: '종결',     color: '#94a3b8', bg: 'rgba(148,163,184,0.15)' },
  };
  const m = map[status] || map.open;
  return (
    <span className="status-badge" style={{
      color: m.color, background: m.bg,
      border: `1px solid ${m.color}55`, padding: '2px 10px', borderRadius: 12,
      fontSize: 'var(--fs-xs)',
    }}>
      {m.label}
    </span>
  );
}

function PriorityBadge({ priority }) {
  const colors = {
    low:    '#94a3b8', normal: '#60a5fa',
    high:   '#fb923c', urgent: '#ef4444',
  };
  const label = { low: '낮음', normal: '보통', high: '높음', urgent: '긴급' }[priority] || priority;
  const c = colors[priority] || '#60a5fa';
  return (
    <span className="status-badge" style={{
      color: c, background: c + '22', border: `1px solid ${c}55`,
      padding: '2px 8px', borderRadius: 8, fontSize: 'var(--fs-xs)',
    }}>{label}</span>
  );
}

function TicketDetailModal({ ticketId, onClose, onChanged }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [reply, setReply] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!ticketId) { setData(null); return; }
    setLoading(true); setError('');
    adminApi.getSupportTicket(ticketId)
      .then((d) => setData(d))
      .catch((e) => setError(e.message || '상세를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [ticketId]);

  async function handleReply(close = false) {
    if (!reply.trim()) { setError('답변 내용을 입력하세요.'); return; }
    setBusy(true); setError('');
    try {
      await adminApi.replySupportTicket(ticketId, { body: reply.trim(), close });
      setReply('');
      onChanged?.();
    } catch (e) {
      setError(e.message || '답변 전송 실패');
    } finally {
      setBusy(false);
    }
  }

  async function handleClose() {
    setBusy(true);
    try {
      await adminApi.patchSupportTicket(ticketId, { status: 'closed' });
      onChanged?.();
    } catch (e) {
      setError(e.message || '종결 실패');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={!!ticketId}
      onClose={busy ? undefined : onClose}
      title={data?.ticket ? `문의 #${data.ticket.id} — ${data.ticket.subject}` : '문의 상세'}
      size="lg"
    >
      {loading && <div className="text-hint">불러오는 중...</div>}
      {error && <div className="error-box">{error}</div>}
      {data && (
        <>
          <div style={{ display: 'flex', gap: 10, marginBottom: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <StatusBadge status={data.ticket.status} />
            <PriorityBadge priority={data.ticket.priority} />
            <span className="text-hint">카테고리: {data.ticket.category}</span>
            <span className="text-hint">·</span>
            <span className="text-hint">접수: {(data.ticket.created_at || '').slice(0, 16)}</span>
            {data.requester && (
              <>
                <span className="text-hint">·</span>
                <span className="text-hint">
                  요청자: {data.requester.company_name || data.requester.email}
                  {' '}({data.requester.kind})
                </span>
              </>
            )}
          </div>

          <div style={{
            background: 'var(--bg-3, #1e1e2e)', padding: 14, borderRadius: 8,
            maxHeight: 360, overflowY: 'auto', marginBottom: 12,
          }}>
            {(data.messages || []).map((m) => (
              <div key={m.id} style={{
                marginBottom: 10, padding: 10, borderRadius: 8,
                background: m.sender === 'admin' ? 'rgba(34,197,94,0.08)' : 'rgba(96,165,250,0.08)',
                borderLeft: `3px solid ${m.sender === 'admin' ? '#22c55e' : '#60a5fa'}`,
              }}>
                <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-hint)', marginBottom: 4 }}>
                  {m.sender === 'admin' ? '운영자' : '요청자'} · {(m.created_at || '').slice(0, 16)}
                </div>
                <div style={{ whiteSpace: 'pre-wrap' }}>{m.body}</div>
              </div>
            ))}
          </div>

          {data.ticket.status !== 'closed' && (
            <>
              <textarea
                rows={5}
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                placeholder={t('admin_support.reply_placeholder', '답변 내용을 입력하세요.')}
                disabled={busy}
                className="form-input"
                style={{ width: '100%', marginBottom: 10 }}
              />
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button className="btn btn-ghost" onClick={handleClose} disabled={busy}>
                  <AlertCircle size={14} />
                  <span>{t('admin_support.close_btn', '종결')}</span>
                </button>
                <button className="btn btn-ghost" onClick={() => handleReply(false)} disabled={busy}>
                  <Send size={14} />
                  <span>{t('admin_support.reply_btn', '답변')}</span>
                </button>
                <button className="btn btn-primary" onClick={() => handleReply(true)} disabled={busy}>
                  <CheckCircle2 size={14} />
                  <span>{t('admin_support.reply_and_close', '답변 + 종결')}</span>
                </button>
              </div>
            </>
          )}
        </>
      )}
    </Modal>
  );
}
