import React, { useEffect, useState, useCallback } from 'react';
import {
  RefreshCw, Plus, Megaphone, Pencil, Trash2, Pin, Send, Eye,
} from 'lucide-react';
import Modal from '../components/Modal.jsx';
import { adminApi } from '../services/admin.js';
import './Beacons.css';

const AUDIENCE_OPTIONS = [
  { value: 'all',        label: '전체 (회원 + 사장 + 직원)' },
  { value: 'users',      label: '앱 사용자만' },
  { value: 'facilities', label: '사장만' },
  { value: 'staff',      label: '직원만' },
];
const AUDIENCE_LABEL = Object.fromEntries(AUDIENCE_OPTIONS.map((o) => [o.value, o.label]));
const AUDIENCE_COLOR = {
  all: '#a371f7', users: '#1f6feb', facilities: '#2ea043', staff: '#d29922',
};

export default function Announcements() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editTarget, setEditTarget] = useState(null);   // null=닫힘, {}=새 글, row=수정
  const [previewTarget, setPreviewTarget] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    adminApi.listAnnouncements()
      .then((data) => setList(data.announcements || []))
      .catch((err) => setError(err.message || '공지를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  async function handleDelete(item) {
    if (!confirm(`공지 "${item.title}"을 삭제하시겠습니까?`)) return;
    try {
      await adminApi.deleteAnnouncement(item.id);
      reload();
    } catch (err) {
      alert(err.message || '삭제에 실패했습니다.');
    }
  }

  async function handleTogglePin(item) {
    try {
      await adminApi.updateAnnouncement(item.id, { pinned: !item.pinned });
      reload();
    } catch (err) {
      alert(err.message || '상단 고정 변경에 실패했습니다.');
    }
  }

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">시스템 공지</h1>
            <p className="sub-title">
              audience(전체/사용자/사장/직원) 별 공지 + 상단 고정 + 푸시 발송.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>새로고침</span>
            </button>
            <button className="btn btn-primary" onClick={() => setEditTarget({})}>
              <Plus size={16} />
              <span>새 공지</span>
            </button>
          </div>
        </div>
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
              <th style={{ width: 32 }}></th>
              <th>제목</th>
              <th>대상</th>
              <th>푸시</th>
              <th>표시 기간</th>
              <th>작성일</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={7} className="row-empty">로딩 중...</td></tr>}
            {!loading && list.length === 0 && (
              <tr><td colSpan={7} className="row-empty">
                작성된 공지가 없습니다. "새 공지" 버튼으로 시작하세요.
              </td></tr>
            )}
            {!loading && list.map((a) => (
              <tr key={a.id}>
                <td>
                  {a.pinned ? <Pin size={16} style={{ color: '#d29922' }} /> : null}
                </td>
                <td>
                  <div style={{ fontWeight: 500 }}>{a.title}</div>
                  <div className="text-hint" style={{ fontSize: '0.8125rem' }}>
                    {(a.body || '').slice(0, 80)}{(a.body || '').length > 80 ? '...' : ''}
                  </div>
                </td>
                <td>
                  <span
                    className="status-pill"
                    style={{
                      background: (AUDIENCE_COLOR[a.audience] || '#8b949e') + '22',
                      color: AUDIENCE_COLOR[a.audience] || '#8b949e',
                    }}
                  >
                    {AUDIENCE_LABEL[a.audience] || a.audience}
                  </span>
                </td>
                <td className="cell-mono">
                  {a.push_sent ? <span style={{ color: '#2ea043' }}>발송됨</span> : '—'}
                </td>
                <td className="cell-mono" style={{ fontSize: '0.8125rem' }}>
                  {a.starts_at?.slice(0, 10) || '—'} ~ {a.ends_at?.slice(0, 10) || '∞'}
                </td>
                <td className="cell-mono">{a.created_at?.slice(0, 10)}</td>
                <td className="cell-actions">
                  <button className="icon-btn" title="미리보기" onClick={() => setPreviewTarget(a)}>
                    <Eye size={15} />
                  </button>
                  <button
                    className="icon-btn"
                    title={a.pinned ? '상단 고정 해제' : '상단 고정'}
                    onClick={() => handleTogglePin(a)}
                    style={{ color: a.pinned ? '#d29922' : undefined }}
                  >
                    <Pin size={15} />
                  </button>
                  <button className="icon-btn" title="수정" onClick={() => setEditTarget(a)}>
                    <Pencil size={15} />
                  </button>
                  <button
                    className="icon-btn"
                    title="삭제"
                    onClick={() => handleDelete(a)}
                    style={{ color: '#da3633' }}
                  >
                    <Trash2 size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <EditModal
        target={editTarget}
        onClose={() => setEditTarget(null)}
        onSaved={() => { setEditTarget(null); reload(); }}
      />
      <PreviewModal
        announcement={previewTarget}
        onClose={() => setPreviewTarget(null)}
      />
    </div>
  );
}


// ── 작성/수정 모달 ───────────────────────────────────────────────────────────
function EditModal({ target, onClose, onSaved }) {
  const isNew = target && !target.id;
  const [form, setForm] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [pushResult, setPushResult] = useState(null);

  useEffect(() => {
    if (!target) return;
    setForm({
      title:    target.title    || '',
      body:     target.body     || '',
      audience: target.audience || 'all',
      pinned:   !!target.pinned,
      starts_at: target.starts_at || '',
      ends_at:   target.ends_at   || '',
      send_push: false,
    });
    setError(''); setPushResult(null);
  }, [target]);

  async function handleSubmit(e) {
    e?.preventDefault?.();
    if (!form.title?.trim() || !form.body?.trim()) {
      setError('제목과 본문을 입력해 주세요.');
      return;
    }
    setBusy(true); setError(''); setPushResult(null);
    try {
      if (isNew) {
        const data = await adminApi.createAnnouncement({
          title:     form.title.trim(),
          body:      form.body.trim(),
          audience:  form.audience,
          pinned:    form.pinned,
          starts_at: form.starts_at || undefined,
          ends_at:   form.ends_at   || undefined,
          send_push: form.send_push,
        });
        if (data.push_result) {
          setPushResult(data.push_result);
          // 푸시 결과 보고 1초 후 닫기
          setTimeout(() => onSaved?.(), 1500);
        } else {
          onSaved?.();
        }
      } else {
        await adminApi.updateAnnouncement(target.id, {
          title:    form.title.trim(),
          body:     form.body.trim(),
          audience: form.audience,
          pinned:   form.pinned,
          starts_at: form.starts_at || null,
          ends_at:   form.ends_at   || null,
        });
        onSaved?.();
      }
    } catch (err) {
      setError(err.message || '저장에 실패했습니다.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={!!target}
      onClose={busy ? undefined : onClose}
      title={isNew ? '새 공지 작성' : `공지 #${target?.id} 수정`}
      size="lg"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={busy}>
            {busy ? '저장 중...' : isNew ? '작성' : '저장'}
          </button>
        </>
      }
    >
      <label className="form-label">
        <span>제목 *</span>
        <input
          type="text"
          value={form.title || ''}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          maxLength={120}
          disabled={busy}
        />
      </label>
      <label className="form-label">
        <span>본문 *</span>
        <textarea
          rows={6}
          value={form.body || ''}
          onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))}
          disabled={busy}
        />
      </label>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }}>
        <label className="form-label">
          <span>대상 audience</span>
          <select
            value={form.audience || 'all'}
            onChange={(e) => setForm((f) => ({ ...f, audience: e.target.value }))}
            disabled={busy}
          >
            {AUDIENCE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </label>
        <label className="form-label" style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0.5rem' }}>
          <input
            type="checkbox"
            checked={!!form.pinned}
            onChange={(e) => setForm((f) => ({ ...f, pinned: e.target.checked }))}
            disabled={busy}
            style={{ width: 'auto', margin: 0 }}
          />
          <span>상단 고정</span>
        </label>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }}>
        <label className="form-label">
          <span>시작 (선택)</span>
          <input
            type="datetime-local"
            value={form.starts_at || ''}
            onChange={(e) => setForm((f) => ({ ...f, starts_at: e.target.value }))}
            disabled={busy}
          />
        </label>
        <label className="form-label">
          <span>종료 (선택)</span>
          <input
            type="datetime-local"
            value={form.ends_at || ''}
            onChange={(e) => setForm((f) => ({ ...f, ends_at: e.target.value }))}
            disabled={busy}
          />
        </label>
      </div>

      {isNew && (
        <label className="form-label" style={{
          display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0.5rem',
          background: 'var(--bg-3)', padding: '0.6rem 0.8rem', borderRadius: 8,
        }}>
          <input
            type="checkbox"
            checked={!!form.send_push}
            onChange={(e) => setForm((f) => ({ ...f, send_push: e.target.checked }))}
            disabled={busy}
            style={{ width: 'auto', margin: 0 }}
          />
          <Send size={15} />
          <span>지금 푸시 알림으로 발송 (audience=users 또는 all 일 때 동작)</span>
        </label>
      )}

      {error && <div className="error-box">{error}</div>}
      {pushResult && (
        <div className="card" style={{ marginTop: '0.75rem', background: 'var(--bg-3)' }}>
          <strong>푸시 발송 결과</strong>
          <div className="text-muted" style={{ fontSize: '0.875rem', marginTop: '0.4rem' }}>
            성공 {pushResult.sent ?? 0} · 실패 {pushResult.failed ?? 0} ·
            토큰 없음 {pushResult.no_tokens ?? 0}
            {pushResult.skipped && <> · skipped: {pushResult.skipped}</>}
          </div>
        </div>
      )}
    </Modal>
  );
}


// ── 미리보기 모달 ────────────────────────────────────────────────────────────
function PreviewModal({ announcement: a, onClose }) {
  return (
    <Modal
      open={!!a}
      onClose={onClose}
      title={a ? `미리보기 — #${a.id}` : ''}
      size="md"
    >
      {a && (
        <div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            marginBottom: '0.75rem',
          }}>
            {a.pinned && <Pin size={16} style={{ color: '#d29922' }} />}
            <Megaphone size={16} className="text-muted" />
            <span
              className="status-pill"
              style={{
                background: (AUDIENCE_COLOR[a.audience] || '#8b949e') + '22',
                color: AUDIENCE_COLOR[a.audience] || '#8b949e',
              }}
            >
              {AUDIENCE_LABEL[a.audience] || a.audience}
            </span>
          </div>
          <h2 style={{ marginTop: 0, marginBottom: '0.75rem' }}>{a.title}</h2>
          <div style={{
            whiteSpace: 'pre-wrap',
            color: 'var(--text)',
            lineHeight: 1.6,
            fontSize: '0.9375rem',
          }}>
            {a.body}
          </div>
          <div className="text-hint" style={{ marginTop: '1rem', fontSize: '0.8125rem' }}>
            작성: {a.created_at} · 푸시: {a.push_sent ? '발송됨' : '미발송'}
          </div>
        </div>
      )}
    </Modal>
  );
}
