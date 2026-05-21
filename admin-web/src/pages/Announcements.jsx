import React, { useEffect, useState, useCallback } from 'react';
import {
  RefreshCw, Plus, Megaphone, Pencil, Trash2, Pin, Send, Eye,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Modal from '../components/Modal.jsx';
import { useDialog } from '../components/DialogProvider.jsx';
import { adminApi } from '../services/admin.js';
import './Beacons.css';

const AUDIENCE_VALUES = ['all', 'users', 'facilities', 'staff'];

export default function Announcements() {
  const { t } = useTranslation();
  const { confirm, alert } = useDialog();

  const AUDIENCE_OPTIONS = AUDIENCE_VALUES.map((v) => ({
    value: v,
    label: t(`notif.audience_${v}`),
  }));
  const AUDIENCE_LABEL = Object.fromEntries(AUDIENCE_OPTIONS.map((o) => [o.value, o.label]));

  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editTarget, setEditTarget] = useState(null);   // null=닫힘, {}=새 글, row=수정
  const [previewTarget, setPreviewTarget] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    adminApi.listAnnouncements()
      .then((data) => setList(data.announcements || []))
      .catch((err) => setError(err.message || t('notif.load_failed')))
      .finally(() => setLoading(false));
  }, [t]);

  useEffect(() => { reload(); }, [reload]);

  async function handleDelete(item) {
    const ok = await confirm({
      title: t('notif.delete_confirm'),
      message: `"${item.title}"`,
      danger: true, confirmText: t('common.delete'),
    });
    if (!ok) return;
    try {
      await adminApi.deleteAnnouncement(item.id);
      reload();
    } catch (err) {
      alert(err.message || t('notif.delete_failed'));
    }
  }

  async function handleTogglePin(item) {
    try {
      await adminApi.updateAnnouncement(item.id, { pinned: !item.pinned });
      reload();
    } catch (err) {
      alert(err.message || t('notif.pin_failed'));
    }
  }

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">{t('notif.page_title')}</h1>
            <p className="sub-title">{t('notif.page_subtitle')}</p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>{t('notif.btn_refresh')}</span>
            </button>
            <button className="btn btn-primary" onClick={() => setEditTarget({})}>
              <Plus size={16} />
              <span>{t('notif.btn_new')}</span>
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
              <th>{t('notif.col_title')}</th>
              <th>{t('notif.col_audience')}</th>
              <th>{t('notif.col_push')}</th>
              <th>{t('notif.col_period')}</th>
              <th>{t('notif.col_created')}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={7} className="row-empty">{t('common.loading')}</td></tr>}
            {!loading && list.length === 0 && (
              <tr><td colSpan={7} className="row-empty">{t('notif.empty_msg')}</td></tr>
            )}
            {!loading && list.map((a) => (
              <tr key={a.id}>
                <td>
                  {a.pinned ? <Pin size={16} style={{ color: 'var(--text-muted)' }} /> : null}
                </td>
                <td>
                  <div style={{ fontWeight: 500 }}>{a.title}</div>
                  <div className="text-hint" style={{ fontSize: 'var(--fs-xs)', marginTop: 2 }}>
                    {(a.body || '').slice(0, 80)}{(a.body || '').length > 80 ? '...' : ''}
                  </div>
                  {a.send_kind === 'marketing' && (
                    <span className="status-badge" style={{
                      marginTop: 4, fontSize: 'var(--fs-xs)',
                      background: 'var(--warning-soft, rgba(234,179,8,0.15))',
                      color: 'var(--warning, #ca8a04)',
                      border: '1px solid rgba(234,179,8,0.3)',
                    }}>
                      {t('notif.send_kind_marketing')}
                    </span>
                  )}
                </td>
                <td>
                  <span className="status-badge neutral">
                    {AUDIENCE_LABEL[a.audience] || a.audience}
                  </span>
                </td>
                <td className="cell-mono">
                  {a.push_sent
                    ? <span style={{ color: 'var(--accent)' }}>{t('notif.push_sent')}</span>
                    : <span className="text-hint">—</span>}
                </td>
                <td className="cell-mono" style={{ fontSize: '0.8125rem' }}>
                  {a.starts_at?.slice(0, 10) || '—'} ~ {a.ends_at?.slice(0, 10) || '∞'}
                </td>
                <td className="cell-mono">{a.created_at?.slice(0, 10)}</td>
                <td className="cell-actions">
                  <button className="icon-btn" title={t('common.edit')} onClick={() => setPreviewTarget(a)}>
                    <Eye size={15} />
                  </button>
                  <button
                    className={`icon-btn${a.pinned ? ' accent' : ''}`}
                    title={a.pinned ? t('notif.pinned_label') : t('notif.pinned_label')}
                    onClick={() => handleTogglePin(a)}
                    style={a.pinned ? { color: 'var(--accent)' } : undefined}
                  >
                    <Pin size={15} />
                  </button>
                  <button className="icon-btn" title={t('common.edit')} onClick={() => setEditTarget(a)}>
                    <Pencil size={15} />
                  </button>
                  <button
                    className="icon-btn danger"
                    title={t('common.delete')}
                    onClick={() => handleDelete(a)}
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
        audienceOptions={AUDIENCE_OPTIONS}
      />
      <PreviewModal
        announcement={previewTarget}
        audienceLabel={AUDIENCE_LABEL}
        onClose={() => setPreviewTarget(null)}
      />
    </div>
  );
}


// ── 작성/수정 모달 ───────────────────────────────────────────────────────────
function EditModal({ target, onClose, onSaved, audienceOptions }) {
  const { t } = useTranslation();
  const isNew = target && !target.id;
  const [form, setForm] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [pushResult, setPushResult] = useState(null);

  useEffect(() => {
    if (!target) return;
    setForm({
      title:     target.title     || '',
      body:      target.body      || '',
      audience:  target.audience  || 'all',
      pinned:    !!target.pinned,
      send_kind: target.send_kind || 'general',
      starts_at: target.starts_at || '',
      ends_at:   target.ends_at   || '',
      send_push: false,
    });
    setError(''); setPushResult(null);
  }, [target]);

  async function handleSubmit(e) {
    e?.preventDefault?.();
    if (!form.title?.trim() || !form.body?.trim()) {
      setError(t('notif.validation_required'));
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
          send_kind: form.send_kind,
          starts_at: form.starts_at || undefined,
          ends_at:   form.ends_at   || undefined,
          send_push: form.send_push,
        });
        if (data.push_result) {
          setPushResult(data.push_result);
          setTimeout(() => onSaved?.(), 1500);
        } else {
          onSaved?.();
        }
      } else {
        await adminApi.updateAnnouncement(target.id, {
          title:     form.title.trim(),
          body:      form.body.trim(),
          audience:  form.audience,
          pinned:    form.pinned,
          send_kind: form.send_kind,
          starts_at: form.starts_at || null,
          ends_at:   form.ends_at   || null,
        });
        onSaved?.();
      }
    } catch (err) {
      setError(err.message || t('notif.save_failed'));
    } finally {
      setBusy(false);
    }
  }

  const isMarketing = form.send_kind === 'marketing';

  return (
    <Modal
      open={!!target}
      onClose={busy ? undefined : onClose}
      title={isNew ? t('notif.modal_new_title') : t('notif.modal_edit_title')}
      size="lg"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>{t('common.cancel')}</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={busy}>
            {busy ? `${t('common.save')}…` : isNew ? t('notif.btn_create') : t('notif.btn_save')}
          </button>
        </>
      }
    >
      {/* 발송 종류 토글 */}
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ fontSize: 'var(--fs-sm)', fontWeight: 500, color: 'var(--text)', marginBottom: 8 }}>
          {t('notif.send_kind_label')}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {['general', 'marketing'].map((kind) => (
            <button
              key={kind}
              type="button"
              onClick={() => setForm((f) => ({ ...f, send_kind: kind }))}
              disabled={busy}
              style={{
                padding: '7px 16px',
                borderRadius: 8,
                fontSize: 'var(--fs-sm)',
                fontWeight: form.send_kind === kind ? 600 : 400,
                background: form.send_kind === kind ? 'var(--accent)' : 'var(--bg-3)',
                color: form.send_kind === kind ? '#000' : 'var(--text-muted)',
                border: `1px solid ${form.send_kind === kind ? 'var(--accent)' : 'var(--border)'}`,
                cursor: busy ? 'not-allowed' : 'pointer',
                transition: 'background 0.12s, color 0.12s',
              }}
            >
              {t(`notif.send_kind_${kind}`)}
            </button>
          ))}
        </div>
        {isMarketing && (
          <div style={{
            marginTop: 10,
            padding: '10px 14px',
            borderRadius: 8,
            background: 'rgba(234,179,8,0.12)',
            border: '1px solid rgba(234,179,8,0.35)',
            color: 'var(--warning, #ca8a04)',
            fontSize: 'var(--fs-sm)',
          }}>
            ⚠ {t('notif.send_kind_warning')}
          </div>
        )}
      </div>

      <label className="form-label">
        <span>{t('notif.title_label')} *</span>
        <input
          type="text"
          value={form.title || ''}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          maxLength={120}
          disabled={busy}
        />
      </label>
      <label className="form-label">
        <span>{t('notif.body_label')} *</span>
        <textarea
          rows={6}
          value={form.body || ''}
          onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))}
          disabled={busy}
        />
      </label>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }}>
        <label className="form-label">
          <span>{t('notif.audience_label')}</span>
          <select
            value={form.audience || 'all'}
            onChange={(e) => setForm((f) => ({ ...f, audience: e.target.value }))}
            disabled={busy}
          >
            {audienceOptions.map((o) => (
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
          <span>{t('notif.pinned_label')}</span>
        </label>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }}>
        <label className="form-label">
          <span>{t('notif.starts_at_label')}</span>
          <input
            type="datetime-local"
            value={form.starts_at || ''}
            onChange={(e) => setForm((f) => ({ ...f, starts_at: e.target.value }))}
            disabled={busy}
          />
        </label>
        <label className="form-label">
          <span>{t('notif.ends_at_label')}</span>
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
          <span>{t('notif.send_push_label')}</span>
        </label>
      )}

      {error && <div className="error-box">{error}</div>}
      {pushResult && (
        <div className="card" style={{ marginTop: '0.75rem', background: 'var(--bg-3)' }}>
          <strong>{t('notif.push_result_title')}</strong>
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
function PreviewModal({ announcement: a, audienceLabel, onClose }) {
  const { t } = useTranslation();
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
            display: 'flex', alignItems: 'center', gap: 8,
            marginBottom: 12,
          }}>
            {a.pinned && <Pin size={16} style={{ color: 'var(--accent)' }} />}
            <Megaphone size={16} className="text-muted" />
            <span className="status-badge neutral">
              {audienceLabel[a.audience] || a.audience}
            </span>
            {a.send_kind === 'marketing' && (
              <span className="status-badge" style={{
                background: 'rgba(234,179,8,0.12)',
                color: 'var(--warning, #ca8a04)',
                border: '1px solid rgba(234,179,8,0.3)',
                fontSize: 'var(--fs-xs)',
              }}>
                {t('notif.send_kind_marketing')}
              </span>
            )}
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
            작성: {a.created_at} · {t('notif.push_sent')}: {a.push_sent ? t('notif.push_sent') : t('notif.push_not_sent')}
          </div>
        </div>
      )}
    </Modal>
  );
}
