import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Bell, Check, X, Send, RefreshCw, Shield, Plus, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { notificationApi } from '../services/notification.js';
import './Beacons.css';

// P11 — main 머지 과정에서 DialogProvider 가 빠진 상태라 window 표준 dialog 로 fallback.
const useDialog = () => ({
  alert:   (msg) => window.alert(msg),
  confirm: (msg) => Promise.resolve(window.confirm(msg)),
});

/**
 * P11 — 알림 부가서비스 어드민 인박스.
 *
 * 좌측: 큐 (필터 = status / ai_review_status)
 * 우측: 상세 + 승인/거절/즉시 dispatch
 * 상단 우측: 금칙어 관리 (모달)
 */
const STATUS_LIST = ['unpaid', 'review', 'pending', 'sent', 'canceled'];
const AI_LIST     = ['auto_pass', 'flagged', 'blocked'];

function statusStyle(s) {
  switch (s) {
    case 'review':  return { background: 'rgba(245,158,11,0.18)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.4)' };
    case 'pending': return { background: 'rgba(59,130,246,0.15)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.4)' };
    case 'sent':    return { background: 'rgba(34,197,94,0.15)',  color: '#22c55e', border: '1px solid rgba(34,197,94,0.4)' };
    case 'unpaid':  return { background: 'rgba(239,68,68,0.15)',  color: '#f87171', border: '1px solid rgba(239,68,68,0.4)' };
    default:        return { background: 'rgba(100,116,139,0.15)', color: '#94a3b8', border: '1px solid rgba(100,116,139,0.3)' };
  }
}

function aiStyle(s) {
  if (s === 'blocked') return { color: '#f87171' };
  if (s === 'flagged') return { color: '#fbbf24' };
  if (s === 'auto_pass') return { color: '#22c55e' };
  return { color: '#94a3b8' };
}

export default function Notifications() {
  const { t } = useTranslation();
  const { alert, confirm } = useDialog();

  const [statusFilter, setStatusFilter] = useState('review');   // 기본: 검토 대기 우선
  const [aiFilter,     setAiFilter]     = useState('');
  const [items,        setItems]        = useState([]);
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState('');

  const [selected,     setSelected]     = useState(null);
  const [detail,       setDetail]       = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [busy,         setBusy]         = useState(false);

  const [showBlock,    setShowBlock]    = useState(false);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    notificationApi.loadQueue({
      status:           statusFilter || undefined,
      ai_review_status: aiFilter || undefined,
    })
      .then((data) => setItems(data.notifications || []))
      .catch((err) => setError(err?.message || '큐를 불러올 수 없습니다.'))
      .finally(() => setLoading(false));
  }, [statusFilter, aiFilter]);

  useEffect(() => { reload(); }, [reload]);

  useEffect(() => {
    if (!selected) { setDetail(null); return; }
    setDetailLoading(true);
    notificationApi.getNotification(selected)
      .then((data) => setDetail(data.notification || data))
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false));
  }, [selected]);

  async function doAction(label, fn) {
    if (busy || !selected) return;
    setBusy(true);
    try {
      await fn(selected);
      const fresh = await notificationApi.getNotification(selected);
      setDetail(fresh.notification || fresh);
      reload();
    } catch (err) {
      alert(err?.message || `${label} 실패`);
    } finally {
      setBusy(false);
    }
  }

  const counts = useMemo(() => {
    const byStatus = {};
    items.forEach((n) => { byStatus[n.status] = (byStatus[n.status] || 0) + 1; });
    return byStatus;
  }, [items]);

  return (
    <div className="modern-page">
      {/* 헤더 */}
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">
              <Bell size={22} style={{ verticalAlign: 'middle', marginRight: 8, color: 'var(--accent)' }} />
              알림 부가서비스 검토
            </h1>
          </div>
          <div className="header-actions" style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost" onClick={() => setShowBlock(true)}>
              <Shield size={16} />
              <span style={{ marginLeft: 4 }}>금칙어 관리</span>
            </button>
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
            </button>
          </div>
        </div>

        {/* 안내 박스 */}
        <div style={{
          marginTop: '0.75rem', padding: '0.75rem 1rem', borderRadius: 10,
          background: 'var(--bg-3)', border: '1px solid var(--border)',
          fontSize: 'var(--fs-sm)', color: 'var(--text-muted)', display: 'flex', gap: '2rem',
        }}>
          <span>매장이 신청한 알림은 AI 자동 검토 후 <strong style={{ color: 'var(--text)' }}>review</strong> 큐로 들어옵니다. 승인 시 예약 시각에 자동 발송됩니다.</span>
        </div>
      </div>

      {/* 필터 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: '1rem', flexWrap: 'wrap' }}>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setSelected(null); }}
          style={{ padding: '7px 12px', borderRadius: 8, background: 'var(--bg-3)', border: '1px solid var(--border)', color: 'var(--text)', fontSize: 'var(--fs-sm)' }}
        >
          <option value="">전체 상태</option>
          {STATUS_LIST.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={aiFilter}
          onChange={(e) => setAiFilter(e.target.value)}
          style={{ padding: '7px 12px', borderRadius: 8, background: 'var(--bg-3)', border: '1px solid var(--border)', color: 'var(--text)', fontSize: 'var(--fs-sm)' }}
        >
          <option value="">AI 전체</option>
          {AI_LIST.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <div style={{ marginLeft: 'auto', fontSize: 'var(--fs-sm)', color: 'var(--text-muted)' }}>
          전체 {items.length}건 · 검토 {counts.review || 0} · 예약 {counts.pending || 0} · 발송 {counts.sent || 0} · 미결제 {counts.unpaid || 0}
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {/* 본문 — 좌측 큐 + 우측 상세 */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '1rem', alignItems: 'start' }}>
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {loading && (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
              {t('common.loading', '로딩 중…')}
            </div>
          )}
          {!loading && items.length === 0 && (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
              알림이 없습니다.
            </div>
          )}
          {!loading && items.map((n) => (
            <div
              key={n.id}
              onClick={() => setSelected(n.id)}
              style={{
                padding: '0.875rem 1rem',
                borderBottom: '1px solid var(--border)',
                cursor: 'pointer',
                background: selected === n.id ? 'rgba(34,197,94,0.08)' : 'transparent',
                borderLeft: selected === n.id ? '3px solid var(--accent)' : '3px solid transparent',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ fontWeight: 500, fontSize: 'var(--fs-sm)', color: 'var(--text)' }}>
                  #{n.id} {n.title}
                </span>
                <span className="status-badge" style={statusStyle(n.status)}>
                  {n.status}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 'var(--fs-xs)' }}>
                <span style={{ color: 'var(--text-muted)' }}>{n.facility_name}</span>
                {n.ai_review_status && (
                  <span style={aiStyle(n.ai_review_status)}>· AI {n.ai_review_status}</span>
                )}
                <span style={{ color: 'var(--text-muted)', marginLeft: 'auto' }}>
                  {(n.scheduled_at || '').slice(0, 16)}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* 상세 */}
        <div className="card" style={{ minHeight: 480 }}>
          {!selected && (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              왼쪽 목록에서 알림을 선택하세요.
            </div>
          )}
          {selected && detailLoading && (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              {t('common.loading', '로딩 중…')}
            </div>
          )}
          {selected && !detailLoading && detail && (
            <div>
              {/* 메타 */}
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--text)', marginBottom: 4 }}>
                  #{detail.id} {detail.title}
                </div>
                <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                  {detail.facility_name} · 예약 {(detail.scheduled_at || '').slice(0, 16)} · 수신자 {detail.recipient_count || 0}명
                </div>
              </div>

              <div style={{ display: 'flex', gap: 12, marginBottom: '1rem', flexWrap: 'wrap' }}>
                <span className="status-badge" style={statusStyle(detail.status)}>{detail.status}</span>
                {detail.ai_review_status && (
                  <span style={{ ...aiStyle(detail.ai_review_status), fontSize: 'var(--fs-xs)', fontWeight: 600 }}>
                    AI: {detail.ai_review_status}
                  </span>
                )}
                {detail.approved_by_admin_id && (
                  <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                    승인 by #{detail.approved_by_admin_id} · {(detail.approved_at || '').slice(0, 16)}
                  </span>
                )}
              </div>

              {detail.ai_review_reason && (
                <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', borderRadius: 8, background: 'var(--bg-3)', border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>AI 검토 사유</div>
                  <div style={{ fontSize: 'var(--fs-sm)' }}>{detail.ai_review_reason}</div>
                </div>
              )}

              {/* 본문 */}
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>본문</div>
                <div style={{
                  padding: '0.75rem 1rem', borderRadius: 8, background: 'var(--bg-3)',
                  border: '1px solid var(--border)', whiteSpace: 'pre-wrap', fontSize: 'var(--fs-sm)', lineHeight: 1.6,
                }}>
                  {detail.body}
                </div>
              </div>

              {/* 수신자 미리보기 */}
              {detail.recipients_preview && detail.recipients_preview.length > 0 && (
                <div style={{ marginBottom: '1rem', fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                  수신자 ID 미리보기: {detail.recipients_preview.slice(0, 20).join(', ')}
                  {detail.recipients_preview.length === 20 && ' ...'}
                </div>
              )}

              {/* 액션 */}
              <div style={{ display: 'flex', gap: 8, marginTop: '1rem', flexWrap: 'wrap' }}>
                {(detail.status === 'review' || detail.status === 'unpaid') && (
                  <button
                    className="btn btn-primary"
                    disabled={busy}
                    onClick={() => doAction('승인', notificationApi.approve)}
                  >
                    <Check size={15} /> <span>승인 → 예약</span>
                  </button>
                )}
                {(detail.status === 'review' || detail.status === 'pending' || detail.status === 'unpaid') && (
                  <button
                    className="btn"
                    style={{ background: 'var(--danger)', color: 'white' }}
                    disabled={busy}
                    onClick={async () => {
                      if (!(await confirm('이 알림을 거부하시겠습니까?'))) return;
                      doAction('거부', notificationApi.reject);
                    }}
                  >
                    <X size={15} /> <span>거부</span>
                  </button>
                )}
                {detail.status === 'pending' && (
                  <button
                    className="btn btn-ghost"
                    disabled={busy}
                    onClick={async () => {
                      if (!(await confirm('지금 즉시 발송합니다. (quota 차감)'))) return;
                      doAction('즉시 발송', notificationApi.dispatch);
                    }}
                  >
                    <Send size={15} /> <span>즉시 발송</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {showBlock && <BlocklistModal onClose={() => setShowBlock(false)} />}
    </div>
  );
}


// ── 금칙어 관리 모달 ──────────────────────────────────────────────────
function BlocklistModal({ onClose }) {
  const { alert, confirm } = useDialog();
  const [rows, setRows]     = useState([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy]     = useState(false);
  const [term, setTerm]     = useState('');
  const [severity, setSeverity] = useState('flag');
  const [note, setNote]     = useState('');

  const reload = useCallback(() => {
    setLoading(true);
    notificationApi.loadBlocklist()
      .then((data) => setRows(data.blocklist || []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  async function add() {
    if (!term.trim() || busy) return;
    setBusy(true);
    try {
      await notificationApi.addBlocklist({ term: term.trim(), severity, note: note.trim() });
      setTerm(''); setNote('');
      reload();
    } catch (err) {
      alert(err?.message || '등록 실패');
    } finally { setBusy(false); }
  }

  async function remove(bid) {
    if (!(await confirm('금칙어를 삭제할까요?'))) return;
    setBusy(true);
    try {
      await notificationApi.deleteBlocklist(bid);
      reload();
    } catch (err) {
      alert(err?.message || '삭제 실패');
    } finally { setBusy(false); }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
    }} onClick={onClose}>
      <div className="card" style={{ width: 'min(560px, 92vw)', maxHeight: '85vh', overflow: 'auto' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.1rem' }}>
            <Shield size={18} style={{ verticalAlign: 'middle', marginRight: 6, color: 'var(--accent)' }} />
            금칙어 관리
          </h2>
          <button className="btn btn-ghost" onClick={onClose}><X size={16} /></button>
        </div>

        {/* 추가 폼 */}
        <div style={{
          display: 'flex', gap: 8, marginBottom: '1rem', padding: '0.75rem',
          background: 'var(--bg-3)', borderRadius: 8, border: '1px solid var(--border)',
        }}>
          <input
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="단어"
            style={{ flex: 1, padding: '7px 10px', borderRadius: 6, background: 'var(--bg-2)', border: '1px solid var(--border)', color: 'var(--text)', fontSize: 'var(--fs-sm)' }}
          />
          <select value={severity} onChange={(e) => setSeverity(e.target.value)}
            style={{ padding: '7px 10px', borderRadius: 6, background: 'var(--bg-2)', border: '1px solid var(--border)', color: 'var(--text)', fontSize: 'var(--fs-sm)' }}>
            <option value="flag">flag (검토)</option>
            <option value="block">block (차단)</option>
          </select>
          <button className="btn btn-primary" onClick={add} disabled={busy || !term.trim()}>
            <Plus size={14} /> <span>추가</span>
          </button>
        </div>
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="메모 (선택)"
          style={{ width: '100%', padding: '7px 10px', borderRadius: 6, background: 'var(--bg-3)', border: '1px solid var(--border)', color: 'var(--text)', fontSize: 'var(--fs-sm)', marginBottom: '1rem', boxSizing: 'border-box' }}
        />

        {/* 목록 */}
        {loading && <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)' }}>로딩 중…</div>}
        {!loading && rows.length === 0 && (
          <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
            등록된 금칙어가 없습니다.
          </div>
        )}
        {!loading && rows.map((r) => (
          <div key={r.id} style={{
            display: 'flex', alignItems: 'center', padding: '0.5rem 0.75rem',
            borderBottom: '1px solid var(--border)', gap: 8,
          }}>
            <span style={{ fontWeight: 500 }}>{r.term}</span>
            <span style={{
              fontSize: 'var(--fs-xs)', padding: '2px 6px', borderRadius: 4,
              ...statusStyle(r.severity === 'block' ? 'unpaid' : 'review'),
            }}>{r.severity}</span>
            {r.note && <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', flex: 1 }}>· {r.note}</span>}
            <button className="btn btn-ghost" onClick={() => remove(r.id)} disabled={busy}
              style={{ marginLeft: 'auto', color: 'var(--danger)' }}>
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
