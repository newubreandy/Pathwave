/**
 * 매장 업종 카테고리 관리 (슈퍼어드민).
 *
 * 사장 가입 시 자유 입력 차단 — 본 페이지에서 추가/수정/비활성화한 카테고리만
 * provider 가입 화면에서 선택 가능.
 *
 * 데이터: 국세청 100대 생활업종 + 자유롭게 신규 추가.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, Plus, Edit2, Trash2, EyeOff, Eye } from 'lucide-react';
import { adminApi } from '../services/admin.js';
import Modal from '../components/Modal.jsx';

const EMPTY = { name: '', group: '기타', sort_order: 0, active: true };

export default function Categories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');
  const [success, setSuccess] = useState('');
  const [draft, setDraft]     = useState(null);
  const [busy, setBusy]       = useState(false);
  const [filter, setFilter]   = useState({ q: '', group: 'all', status: 'all' });

  const reload = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const res = await adminApi.listCategories();
      setCategories(res.categories || []);
    } catch (e) {
      setError(e?.message || '불러오기 실패');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const filtered = categories.filter((c) => {
    if (filter.q && !c.name.toLowerCase().includes(filter.q.toLowerCase())) return false;
    if (filter.group !== 'all' && (c.group || '기타') !== filter.group) return false;
    if (filter.status === 'active'  && !c.active) return false;
    if (filter.status === 'inactive' &&  c.active) return false;
    return true;
  });

  const groups = Array.from(new Set(categories.map((c) => c.group || '기타'))).sort();
  const summary = {
    total: categories.length,
    active: categories.filter((c) => c.active).length,
    inactive: categories.filter((c) => !c.active).length,
  };

  async function save() {
    if (!draft) return;
    setBusy(true); setError(''); setSuccess('');
    try {
      const payload = {
        name: draft.name.trim(),
        group: (draft.group || '기타').trim(),
        sort_order: Number(draft.sort_order) || 0,
        active: !!draft.active,
      };
      if (!payload.name) throw new Error('이름 필수.');
      if (draft.id) {
        await adminApi.updateCategory(draft.id, payload);
        setSuccess('수정되었습니다.');
      } else {
        await adminApi.createCategory(payload);
        setSuccess('추가되었습니다.');
      }
      setDraft(null);
      reload();
    } catch (e) {
      setError(e?.message || '저장 실패');
    } finally {
      setBusy(false);
    }
  }

  async function toggleActive(cat) {
    setBusy(true); setError(''); setSuccess('');
    try {
      if (cat.active) {
        await adminApi.deactivateCategory(cat.id);
        setSuccess(`'${cat.name}' 비활성화 (가입 화면에서 제외)`);
      } else {
        await adminApi.updateCategory(cat.id, { active: true });
        setSuccess(`'${cat.name}' 재활성화`);
      }
      reload();
    } catch (e) {
      setError(e?.message || '변경 실패');
    } finally {
      setBusy(false);
    }
  }

  async function hardDelete(cat) {
    if (!window.confirm(`'${cat.name}' 완전 삭제? (복구 불가)`)) return;
    setBusy(true); setError(''); setSuccess('');
    try {
      await adminApi.hardDeleteCategory(cat.id);
      setSuccess('완전 삭제됨');
      reload();
    } catch (e) {
      setError(e?.message || '삭제 실패');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex',
            alignItems: 'center', justifyContent: 'space-between',
            marginBottom: '1rem' }}>
        <div>
          <h1 className="page-title">매장 업종 카테고리</h1>
          <p className="page-subtitle">
            사장 가입 시 선택 가능한 업종 목록 (자유 입력 금지). 국세청 100대 생활업종 시드.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <button className="btn btn-primary"
                  onClick={() => setDraft({ ...EMPTY, sort_order: (categories.length + 1) * 10 })}
                  disabled={busy}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
                  aria-label="신규 카테고리">
            <Plus size={14} aria-hidden="true" /> 신규
          </button>
          <button className="btn btn-ghost" onClick={reload}
                  disabled={loading} aria-label="새로고침">
            <RefreshCw size={16} className={loading ? 'spin' : ''} aria-hidden="true" />
          </button>
        </div>
      </div>

      {/* 요약 + 필터 */}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center',
                    flexWrap: 'wrap', marginBottom: '1rem',
                    fontSize: 'var(--fs-sm)' }}>
        <div style={{ color: 'var(--text-muted)' }}>
          총 <strong style={{ color: 'var(--text)' }}>{summary.total}</strong> ·
          활성 <strong style={{ color: 'var(--accent)' }}>{summary.active}</strong> ·
          비활성 <span>{summary.inactive}</span>
        </div>
        <input value={filter.q}
               onChange={(e) => setFilter({ ...filter, q: e.target.value })}
               placeholder="검색"
               style={{ width: 160 }} />
        <select value={filter.group}
                onChange={(e) => setFilter({ ...filter, group: e.target.value })}>
          <option value="all">전체 그룹</option>
          {groups.map((g) => <option key={g} value={g}>{g}</option>)}
        </select>
        <select value={filter.status}
                onChange={(e) => setFilter({ ...filter, status: e.target.value })}>
          <option value="all">전체 상태</option>
          <option value="active">활성</option>
          <option value="inactive">비활성</option>
        </select>
      </div>

      {error   && <div className="error-box" style={{ marginBottom: '0.75rem' }}>{error}</div>}
      {success && <div style={{ marginBottom: '0.75rem', padding: '0.5rem 0.75rem',
                                background: 'var(--accent-soft)',
                                border: '1px solid var(--accent)', borderRadius: 6,
                                color: 'var(--accent)' }}>{success}</div>}

      <div style={{ overflowX: 'auto', border: '1px solid var(--border)',
                    borderRadius: 10 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse',
                        fontSize: 'var(--fs-sm)' }}>
          <thead>
            <tr style={{ background: 'var(--bg-3)' }}>
              <Th>그룹</Th><Th>순서</Th><Th>이름</Th><Th>상태</Th><Th></Th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr key={c.id} style={{ borderTop: '1px solid var(--border)',
                                       opacity: c.active ? 1 : 0.55 }}>
                <Td><Badge color="var(--text-muted)">{c.group || '기타'}</Badge></Td>
                <Td style={{ width: 60 }}>{c.sort_order}</Td>
                <Td><strong>{c.name}</strong></Td>
                <Td>
                  {c.active
                    ? <Badge color="var(--accent)">활성</Badge>
                    : <Badge color="var(--text-muted)">비활성</Badge>}
                </Td>
                <Td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                  <button className="btn btn-ghost" onClick={() => setDraft({ ...c })}
                          disabled={busy} style={{ padding: '4px 8px' }}
                          aria-label="수정">
                    <Edit2 size={14} aria-hidden="true" />
                  </button>
                  <button className="btn btn-ghost" onClick={() => toggleActive(c)}
                          disabled={busy} style={{ padding: '4px 8px' }}
                          aria-label={c.active ? '비활성화' : '활성화'}>
                    {c.active ? <EyeOff size={14} aria-hidden="true" /> : <Eye size={14} aria-hidden="true" />}
                  </button>
                  <button className="btn btn-ghost" onClick={() => hardDelete(c)}
                          disabled={busy}
                          style={{ padding: '4px 8px', color: 'var(--danger)' }}
                          aria-label="완전 삭제">
                    <Trash2 size={14} aria-hidden="true" />
                  </button>
                </Td>
              </tr>
            ))}
            {!loading && filtered.length === 0 && (
              <tr><Td colSpan={5} style={{ textAlign: 'center', padding: '2rem',
                    color: 'var(--text-muted)' }}>
                조건에 맞는 카테고리가 없습니다.
              </Td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Draft 모달 */}
      {draft && (
        <Modal open={true} onClose={busy ? undefined : () => setDraft(null)}
               size="sm" title={draft.id ? '카테고리 수정' : '카테고리 신규'}
               footer={
                 <>
                   <button className="btn btn-ghost" onClick={() => setDraft(null)}
                           disabled={busy}>취소</button>
                   <button className="btn btn-primary" onClick={save}
                           disabled={busy || !draft.name?.trim()}>
                     {busy ? '저장 중...' : (draft.id ? '저장' : '추가')}
                   </button>
                 </>
               }>
          <label className="form-label">
            <span>이름 * (60자 이내)</span>
            <input value={draft.name}
                   onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                   maxLength={60} disabled={busy} autoFocus />
          </label>
          <label className="form-label">
            <span>그룹 (음식/소매/서비스 등)</span>
            <input value={draft.group || ''}
                   onChange={(e) => setDraft({ ...draft, group: e.target.value })}
                   disabled={busy} placeholder="예: 음식" />
          </label>
          <label className="form-label">
            <span>정렬 순서</span>
            <input type="number" value={draft.sort_order || 0}
                   onChange={(e) => setDraft({ ...draft, sort_order: e.target.value })}
                   disabled={busy} />
          </label>
          {draft.id && (
            <label style={{ display: 'flex', gap: '0.4rem', alignItems: 'center',
                            marginTop: '0.5rem' }}>
              <input type="checkbox" checked={draft.active}
                     onChange={(e) => setDraft({ ...draft, active: e.target.checked })}
                     disabled={busy} />
              <span>활성 (사장 가입 화면 노출)</span>
            </label>
          )}
        </Modal>
      )}
    </div>
  );
}

function Th({ children }) {
  return <th style={{ padding: '0.75rem 0.85rem', textAlign: 'left',
                      fontWeight: 600, color: 'var(--text-secondary)' }}>{children}</th>;
}
function Td({ children, ...rest }) {
  return <td style={{ padding: '0.75rem 0.85rem' }} {...rest}>{children}</td>;
}
function Badge({ color, children }) {
  return <span style={{ display: 'inline-block', padding: '2px 8px',
                        borderRadius: 999, fontSize: 'var(--fs-xs)',
                        border: `1px solid ${color}`, color }}>
    {children}
  </span>;
}
