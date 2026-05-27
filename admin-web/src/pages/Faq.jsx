import React, { useEffect, useState, useCallback } from 'react';
import { BookOpen, Plus, RefreshCw, Pencil, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Modal from '../components/Modal.jsx';
import { supportApi } from '../services/support.js';
import { useConfirm } from '../hooks/useConfirm.jsx';
import './Beacons.css';

const KIND_TABS = [
  { value: 'user',     label: '사용자 FAQ' },
  { value: 'provider', label: '사장님 FAQ' },
];

export default function Faq() {
  const { t } = useTranslation();
  const { confirm, alert: alertModal, modal: confirmModalEl } = useConfirm();
  const [kind, setKind]   = useState('user');
  const [faqs, setFaqs]   = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [editTarget, setEditTarget] = useState(null); // null=닫힘 / {}=신규 / row=수정
  const [toggling, setToggling] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    supportApi.loadFaqs({ kind })
      .then((data) => setFaqs(data.faqs || data || []))
      .catch((err) => setError(err.message || t('faq.empty')))
      .finally(() => setLoading(false));
  }, [kind, t]);

  useEffect(() => { reload(); }, [reload]);

  async function handleDelete(faq) {
    const ok = await confirm({
      title: 'FAQ 삭제',
      desc:  `FAQ #${faq.id} 를 삭제하시겠습니까?\n"${faq.question}"`,
      confirmText: '삭제',
    });
    if (!ok) return;
    try {
      await supportApi.deleteFaq(faq.id);
      reload();
    } catch (err) {
      await alertModal({ title: '삭제 실패', desc: err.message || t('common.delete') });
    }
  }

  async function handleToggleActive(faq) {
    setToggling(faq.id);
    try {
      await supportApi.patchFaq(faq.id, { active: !faq.active });
      reload();
    } catch (err) {
      await alertModal({ title: '오류', desc: err.message });
    } finally {
      setToggling(null);
    }
  }

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">
              <BookOpen size={22} style={{ verticalAlign: 'middle', marginRight: 8, color: 'var(--accent)' }} />
              {t('faq.title')}
            </h1>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
            </button>
            <button className="btn btn-primary" onClick={() => setEditTarget({})}>
              <Plus size={16} />
              <span>FAQ 추가</span>
            </button>
          </div>
        </div>
      </div>

      {/* 탭 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: '1rem' }}>
        {KIND_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setKind(tab.value)}
            style={{
              padding: '7px 18px',
              borderRadius: 8,
              fontWeight: kind === tab.value ? 600 : 400,
              background: kind === tab.value ? 'var(--accent)' : 'var(--bg-3)',
              color: kind === tab.value ? '#000' : 'var(--text-muted)',
              border: `1px solid ${kind === tab.value ? 'var(--accent)' : 'var(--border)'}`,
              cursor: 'pointer',
              fontSize: 'var(--fs-sm)',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 50 }}>#</th>
              <th>질문</th>
              <th style={{ width: 120 }}>카테고리</th>
              <th style={{ width: 80 }}>순서</th>
              <th style={{ width: 70 }}>노출</th>
              <th style={{ width: 100 }}></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={6} className="row-empty">{t('common.loading')}</td></tr>
            )}
            {!loading && faqs.length === 0 && (
              <tr><td colSpan={6} className="row-empty">{t('faq.empty')}</td></tr>
            )}
            {!loading && faqs.map((faq) => (
              <tr key={faq.id}>
                <td className="cell-mono" style={{ color: 'var(--text-muted)' }}>{faq.id}</td>
                <td>
                  <div style={{ fontWeight: 500, fontSize: 'var(--fs-sm)', color: 'var(--text)' }}>
                    {faq.question}
                  </div>
                  <div className="text-hint" style={{ fontSize: 'var(--fs-xs)', marginTop: 2 }}>
                    {(faq.answer || '').slice(0, 80)}{(faq.answer || '').length > 80 ? '…' : ''}
                  </div>
                </td>
                <td>
                  {faq.category && (
                    <span className="status-badge neutral" style={{ fontSize: 'var(--fs-xs)' }}>
                      {faq.category}
                    </span>
                  )}
                </td>
                <td className="cell-mono">{faq.sort_order ?? '—'}</td>
                <td>
                  <button
                    className="icon-btn"
                    onClick={() => handleToggleActive(faq)}
                    disabled={toggling === faq.id}
                    title={faq.active ? '노출 중 (클릭하여 숨김)' : '숨김 (클릭하여 노출)'}
                    style={{ color: faq.active ? 'var(--accent)' : 'var(--text-muted)' }}
                  >
                    {faq.active ? <ToggleRight size={20} /> : <ToggleLeft size={20} />}
                  </button>
                </td>
                <td className="cell-actions">
                  <button
                    className="icon-btn"
                    title={t('common.edit')}
                    onClick={() => setEditTarget(faq)}
                  >
                    <Pencil size={15} />
                  </button>
                  <button
                    className="icon-btn danger"
                    title={t('common.delete')}
                    onClick={() => handleDelete(faq)}
                  >
                    <Trash2 size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <FaqModal
        target={editTarget}
        defaultKind={kind}
        onClose={() => setEditTarget(null)}
        onSaved={() => { setEditTarget(null); reload(); }}
      />
      {confirmModalEl}
    </div>
  );
}

// ── FAQ 추가/수정 모달 ────────────────────────────────────────────────────────
function FaqModal({ target, defaultKind, onClose, onSaved }) {
  const { t } = useTranslation();
  const isNew = target && !target.id;
  const [form, setForm] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!target) return;
    setForm({
      kind:       target.kind       || defaultKind || 'user',
      category:   target.category   || '',
      question:   target.question   || '',
      answer:     target.answer     || '',
      sort_order: target.sort_order ?? 0,
      lang:       target.lang       || 'ko',
    });
    setError('');
  }, [target, defaultKind]);

  async function handleSubmit() {
    if (!form.question?.trim() || !form.answer?.trim()) {
      setError('질문과 답변을 입력해 주세요.');
      return;
    }
    setBusy(true); setError('');
    try {
      if (isNew) {
        await supportApi.addFaq({
          kind:       form.kind,
          category:   form.category || undefined,
          question:   form.question.trim(),
          answer:     form.answer.trim(),
          sort_order: Number(form.sort_order) || 0,
          lang:       form.lang,
        });
      } else {
        await supportApi.patchFaq(target.id, {
          category:   form.category || undefined,
          question:   form.question.trim(),
          answer:     form.answer.trim(),
          sort_order: Number(form.sort_order) || 0,
        });
      }
      onSaved?.();
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
      title={isNew ? 'FAQ 추가' : 'FAQ 수정'}
      size="lg"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>{t('common.cancel')}</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={busy}>
            {busy ? `${t('common.save')}…` : isNew ? t('common.confirm') : t('common.save')}
          </button>
        </>
      }
    >
      {isNew && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }}>
          <label className="form-label">
            <span>종류</span>
            <select
              value={form.kind || 'user'}
              onChange={(e) => setForm((f) => ({ ...f, kind: e.target.value }))}
              disabled={busy}
            >
              <option value="user">사용자</option>
              <option value="provider">사장님</option>
            </select>
          </label>
          <label className="form-label">
            <span>언어</span>
            <select
              value={form.lang || 'ko'}
              onChange={(e) => setForm((f) => ({ ...f, lang: e.target.value }))}
              disabled={busy}
            >
              <option value="ko">한국어</option>
              <option value="en">English</option>
            </select>
          </label>
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '0.875rem', alignItems: 'end' }}>
        <label className="form-label">
          <span>카테고리 (선택)</span>
          <input
            type="text"
            value={form.category || ''}
            onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
            placeholder="예: 예약, 결제, 이용방법"
            disabled={busy}
          />
        </label>
        <label className="form-label" style={{ minWidth: 90 }}>
          <span>정렬 순서</span>
          <input
            type="number"
            value={form.sort_order ?? 0}
            onChange={(e) => setForm((f) => ({ ...f, sort_order: e.target.value }))}
            min={0}
            disabled={busy}
          />
        </label>
      </div>
      <label className="form-label">
        <span>질문 *</span>
        <input
          type="text"
          value={form.question || ''}
          onChange={(e) => setForm((f) => ({ ...f, question: e.target.value }))}
          maxLength={300}
          disabled={busy}
        />
      </label>
      <label className="form-label">
        <span>답변 *</span>
        <textarea
          rows={6}
          value={form.answer || ''}
          onChange={(e) => setForm((f) => ({ ...f, answer: e.target.value }))}
          disabled={busy}
        />
      </label>
      {error && <div className="error-box">{error}</div>}
    </Modal>
  );
}
