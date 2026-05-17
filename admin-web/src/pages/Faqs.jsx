import React, { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { RefreshCw, Plus, Pencil, Trash2 } from 'lucide-react';
import Modal from '../components/Modal.jsx';
import { adminApi } from '../services/admin.js';

const KIND_TABS = ['user', 'provider'];

export default function Faqs() {
  const { t } = useTranslation();

  const [kind, setKind] = useState('user');
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editTarget, setEditTarget] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    adminApi.listFaqsAdmin({ kind, lang: 'ko' })
      .then((d) => setList(d.faqs || []))
      .catch((e) => setError(e.message || 'FAQ 를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [kind]);

  useEffect(() => { reload(); }, [reload]);

  async function handleDelete(item) {
    if (!confirm(t('admin_support.delete_confirm', '정말 삭제하시겠습니까?'))) return;
    try { await adminApi.deleteFaq(item.id); reload(); }
    catch (e) { alert(e.message || '삭제 실패'); }
  }

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">{t('admin_support.faq_title', 'FAQ 관리')}</h1>
            <p className="sub-title">
              사용자/사장님 FAQ 를 분리해 관리합니다. 한국어 입력 후
              i18n 자동 번역 메뉴에서 22 개 언어 일괄 번역하세요.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>새로고침</span>
            </button>
            <button className="btn btn-primary" onClick={() => setEditTarget({ kind })}>
              <Plus size={16} />
              <span>{t('admin_support.faq_new', 'FAQ 추가')}</span>
            </button>
          </div>
        </div>
      </div>

      <div className="card" style={{ display: 'flex', gap: 8, padding: 12, marginBottom: 12 }}>
        {KIND_TABS.map((k) => (
          <button
            key={k}
            onClick={() => setKind(k)}
            className={`btn ${kind === k ? 'btn-primary' : 'btn-ghost'}`}
          >
            {k === 'user'
              ? t('admin_support.faq_kind_user', '사용자 FAQ')
              : t('admin_support.faq_kind_provider', '사장님 FAQ')}
          </button>
        ))}
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
              <th>{t('admin_support.faq_q_label', '질문')}</th>
              <th>카테고리</th>
              <th>{t('admin_support.faq_active', '공개')}</th>
              <th>정렬</th>
              <th>관리</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={6} className="row-empty">불러오는 중...</td></tr>}
            {!loading && list.length === 0 && (
              <tr><td colSpan={6} className="row-empty">등록된 FAQ 가 없습니다.</td></tr>
            )}
            {!loading && list.map((f) => (
              <tr key={f.id}>
                <td className="cell-mono">{f.id}</td>
                <td>
                  <div style={{ fontWeight: 500 }}>{f.question}</div>
                  <div className="text-hint" style={{ fontSize: 'var(--fs-xs)', marginTop: 2 }}>
                    {(f.answer || '').slice(0, 100)}{(f.answer || '').length > 100 ? '...' : ''}
                  </div>
                </td>
                <td>{f.category}</td>
                <td>{f.active ? '공개' : '비공개'}</td>
                <td className="cell-mono">{f.sort_order}</td>
                <td className="cell-actions">
                  <button className="icon-btn" onClick={() => setEditTarget(f)}>
                    <Pencil size={15} />
                  </button>
                  <button className="icon-btn danger" onClick={() => handleDelete(f)}>
                    <Trash2 size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <FaqEditModal
        target={editTarget}
        onClose={() => setEditTarget(null)}
        onSaved={() => { setEditTarget(null); reload(); }}
      />
    </div>
  );
}

function FaqEditModal({ target, onClose, onSaved }) {
  const { t } = useTranslation();
  const isNew = target && !target.id;
  const [form, setForm] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!target) return;
    setForm({
      kind:       target.kind     || 'user',
      category:   target.category || 'usage',
      question:   target.question || '',
      answer:     target.answer   || '',
      lang:       target.lang     || 'ko',
      sort_order: target.sort_order ?? 0,
      active:     target.active   ?? 1,
    });
    setError('');
  }, [target]);

  async function handleSave() {
    if (!form.question?.trim() || !form.answer?.trim() || !form.category?.trim()) {
      setError('카테고리/질문/답변 모두 필수입니다.');
      return;
    }
    setBusy(true); setError('');
    try {
      if (isNew) {
        await adminApi.createFaq({
          kind:       form.kind,
          category:   form.category.trim(),
          question:   form.question.trim(),
          answer:     form.answer.trim(),
          lang:       form.lang || 'ko',
          sort_order: Number(form.sort_order) || 0,
          active:     !!form.active,
        });
      } else {
        await adminApi.updateFaq(target.id, {
          category:   form.category.trim(),
          question:   form.question.trim(),
          answer:     form.answer.trim(),
          lang:       form.lang || 'ko',
          sort_order: Number(form.sort_order) || 0,
          active:     !!form.active,
        });
      }
      onSaved?.();
    } catch (e) {
      setError(e.message || '저장 실패');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={!!target}
      onClose={busy ? undefined : onClose}
      title={isNew ? t('admin_support.faq_new', 'FAQ 추가') : t('admin_support.faq_edit', 'FAQ 수정')}
      size="lg"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={busy}>
            {busy ? '저장 중...' : '저장'}
          </button>
        </>
      }
    >
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <label className="form-label">
          <span>대상</span>
          <select
            value={form.kind || 'user'}
            onChange={(e) => setForm((f) => ({ ...f, kind: e.target.value }))}
            disabled={!isNew || busy}
          >
            <option value="user">사용자</option>
            <option value="provider">사장님</option>
          </select>
        </label>
        <label className="form-label">
          <span>카테고리 코드</span>
          <input
            type="text"
            value={form.category || ''}
            onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
            placeholder="usage / beacon / coupon / payment / etc"
            disabled={busy}
          />
        </label>
      </div>
      <label className="form-label">
        <span>{t('admin_support.faq_q_label', '질문')} *</span>
        <input
          type="text"
          value={form.question || ''}
          onChange={(e) => setForm((f) => ({ ...f, question: e.target.value }))}
          disabled={busy}
        />
      </label>
      <label className="form-label">
        <span>{t('admin_support.faq_a_label', '답변')} *</span>
        <textarea
          rows={8}
          value={form.answer || ''}
          onChange={(e) => setForm((f) => ({ ...f, answer: e.target.value }))}
          disabled={busy}
        />
      </label>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        <label className="form-label">
          <span>{t('admin_support.faq_lang', '언어')}</span>
          <input
            type="text"
            value={form.lang || 'ko'}
            onChange={(e) => setForm((f) => ({ ...f, lang: e.target.value }))}
            disabled={busy}
          />
        </label>
        <label className="form-label">
          <span>정렬</span>
          <input
            type="number"
            value={form.sort_order ?? 0}
            onChange={(e) => setForm((f) => ({ ...f, sort_order: e.target.value }))}
            disabled={busy}
          />
        </label>
        <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input
            type="checkbox"
            checked={!!form.active}
            onChange={(e) => setForm((f) => ({ ...f, active: e.target.checked }))}
            disabled={busy}
            style={{ width: 'auto' }}
          />
          <span>{t('admin_support.faq_active', '공개')}</span>
        </label>
      </div>
      {error && <div className="error-box">{error}</div>}
    </Modal>
  );
}
