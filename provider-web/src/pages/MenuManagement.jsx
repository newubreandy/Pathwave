/**
 * P-026 — 매장 메뉴 OCR + 자동번역 (D-4-b).
 *
 * 사장이 메뉴판 사진 업로드 → 백엔드 OCR (GCV/stub) → items 추출 →
 * 인라인 표에서 수정/추가/삭제 → 외국인 사용자에게 자동 번역으로 노출.
 *
 * 가격 정책
 * --------
 * - 항상 원화 (₩/원/KRW) — 외국 통화 입력 시 백엔드가 422 거부
 * - placeholder/안내문에 "원화 단위 필수" 명시
 * - 입력값 단위 없으면 백엔드가 자동으로 "원" 붙임
 *
 * 흐름
 * ----
 * 1) 매장 ID 자동 fetch (StoreService.list 첫 번째)
 * 2) 현재 ko 메뉴 목록 표시
 * 3) [사진 업로드] 또는 [+ 수동 항목 추가]
 * 4) 인라인 편집 → 저장 (PATCH)
 * 5) 삭제 → 즉시 (DELETE)
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  Camera, Plus, RefreshCw, Save, Trash2, AlertTriangle, Image as ImageIcon,
} from 'lucide-react';
import StoreService from '../services/store/StoreService';
import MenuService from '../services/store/MenuService';
import PwModal, { PwField } from '../components/common/PwModal';
import PwPageHeader from '../components/common/PwPageHeader';
import PwInfoBanner from '../components/common/PwInfoBanner';
import { useConfirm } from '../hooks/useConfirm';

const EMPTY_ITEM = { name: '', price: '', description: '', sort_order: 0 };

export default function MenuManagement() {
  const { confirm, modal: confirmModalEl } = useConfirm();
  const [facility, setFacility] = useState(null);
  const [items, setItems]       = useState([]);
  const [loading, setLoading]   = useState(true);
  const [uploading, setUploading] = useState(false);
  const [busy, setBusy]         = useState(false);
  const [error, setError]       = useState('');
  const [success, setSuccess]   = useState('');
  const [draft, setDraft]       = useState(null);   // {id?, name, price, description, sort_order}
  const [replace, setReplace]   = useState(false);

  const fid = facility?.id;

  const reload = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const fs = await StoreService.list();
      const my = (fs?.facilities || fs?.items || [])[0];
      if (!my) throw new Error('매장을 먼저 등록해 주세요.');
      setFacility(my);
      const res = await MenuService.list(my.id, 'ko');
      setItems((res?.items || []).sort(
        (a, b) => (a.sort_order || 0) - (b.sort_order || 0) || a.id - b.id
      ));
    } catch (e) {
      setError(e?.message || '불러오기 실패');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  async function onFilePick(e) {
    const file = e.target?.files?.[0];
    if (!file || !fid) return;
    e.target.value = '';  // 같은 파일 재선택 가능
    if (file.size > 5 * 1024 * 1024) {
      setError('이미지는 5MB 이하여야 합니다.'); return;
    }
    setUploading(true); setError(''); setSuccess('');
    try {
      const image_b64 = await MenuService.fileToBase64(file);
      const res = await MenuService.uploadImage(fid, { image_b64, replace });
      setSuccess(`OCR 완료 — ${res.item_count}건 추출됨 (provider: ${res.provider})`);
      reload();
    } catch (e) {
      setError(e?.message || '업로드 실패');
    } finally {
      setUploading(false);
    }
  }

  async function saveDraft() {
    if (!fid || !draft) return;
    setBusy(true); setError(''); setSuccess('');
    try {
      const payload = {
        name:        draft.name.trim(),
        price:       (draft.price || '').trim(),
        description: (draft.description || '').trim(),
        sort_order:  Number(draft.sort_order) || 0,
      };
      if (!payload.name) throw new Error('이름 필수.');
      if (draft.id) {
        await MenuService.updateItem(draft.id, payload);
        setSuccess('수정되었습니다.');
      } else {
        await MenuService.createItem(fid, payload);
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

  async function del(item) {
    const ok = await confirm({
      title: '메뉴 삭제',
      desc:  `"${item.name}" 삭제하시겠습니까?\n(연결된 외국어 번역도 함께 제거됩니다)`,
      confirmText: '삭제',
    });
    if (!ok) return;
    setBusy(true); setError(''); setSuccess('');
    try {
      await MenuService.deleteItem(item.id);
      setSuccess('삭제되었습니다.');
      reload();
    } catch (e) {
      setError(e?.message || '삭제 실패');
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center',
                         color: 'var(--pw-text-muted)' }}>불러오는 중...</div>;
  }
  if (error && !facility) {
    return <div className="status-error" style={{ margin: '2rem' }}>{error}</div>;
  }

  return (
    <div style={{ padding: '1.5rem', maxWidth: 960, margin: '0 auto' }}>
      <PwPageHeader
        icon={ImageIcon}
        title="매장 메뉴 관리"
        subtitle="메뉴판 사진을 업로드하면 자동으로 항목이 추출되고, 외국인 사용자에게는 자동 번역으로 제공됩니다."
      />

      <PwInfoBanner variant="warn" icon={AlertTriangle}>
        가격은 <strong>원화 (KRW)</strong> 만 사용. 외국 통화 ($¥€£) 는 자동 거부됩니다.
        숫자만 입력해도 자동으로 "원" 단위 붙습니다.
      </PwInfoBanner>

      {/* 업로드 액션 */}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center',
                    marginBottom: '1rem', flexWrap: 'wrap' }}>
        <label className="pw-btn" style={{ cursor: 'pointer',
                display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
                opacity: uploading ? 0.5 : 1 }}>
          <Camera size={14} aria-hidden="true" />
          {uploading ? '업로드/OCR 중...' : '메뉴판 사진 업로드 (OCR)'}
          <input type="file" accept="image/*" onChange={onFilePick}
                 disabled={uploading} style={{ display: 'none' }} />
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem',
                        color: 'var(--pw-text-muted)',
                        fontSize: 'var(--pw-fs-sm)' }}>
          <input type="checkbox" checked={replace}
                 onChange={(e) => setReplace(e.target.checked)}
                 disabled={uploading} />
          기존 메뉴 교체 (체크 안하면 추가)
        </label>
        <button className="pw-btn pw-btn--ghost"
                onClick={() => setDraft({ ...EMPTY_ITEM, sort_order: (items[items.length - 1]?.sort_order || 0) + 10 })}
                disabled={busy || uploading}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
          <Plus size={14} aria-hidden="true" /> 수동 추가
        </button>
        <button className="pw-btn pw-btn--ghost"
                onClick={reload} disabled={busy || uploading}
                aria-label="새로고침">
          <RefreshCw size={14} aria-hidden="true" />
        </button>
        <div style={{ marginLeft: 'auto', color: 'var(--pw-text-muted)',
                      fontSize: 'var(--pw-fs-sm)' }}>
          총 <strong style={{ color: 'var(--pw-text)' }}>{items.length}</strong>개 항목
        </div>
      </div>

      {error   && <div className="status-error"   style={{ marginBottom: '0.75rem' }}>{error}</div>}
      {success && <div className="status-success" style={{ marginBottom: '0.75rem' }}>{success}</div>}

      {/* 표 */}
      <div style={{ overflowX: 'auto', border: '1px solid var(--pw-border)',
                    borderRadius: 10 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse',
                        fontSize: 'var(--pw-fs-sm)' }}>
          <thead>
            <tr style={{ background: 'var(--pw-bg-3)' }}>
              <Th>순서</Th>
              <Th>이름</Th>
              <Th>가격</Th>
              <Th>설명</Th>
              <Th>출처</Th>
              <Th></Th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id} style={{ borderTop: '1px solid var(--pw-border)' }}>
                <Td style={{ width: 60 }}>{it.sort_order}</Td>
                <Td><strong>{it.name}</strong></Td>
                <Td><code>{it.price || '—'}</code></Td>
                <Td style={{ color: 'var(--pw-text-muted)' }}>{it.description || '—'}</Td>
                <Td>
                  <Badge color={it.source === 'ocr' ? 'var(--pw-primary)' : 'var(--pw-text-muted)'}>
                    {it.source}
                  </Badge>
                </Td>
                <Td style={{ width: 110, textAlign: 'right', whiteSpace: 'nowrap' }}>
                  <button className="pw-btn pw-btn--ghost"
                          onClick={() => setDraft({ ...it })}
                          disabled={busy}
                          style={{ padding: '4px 8px' }}>
                    수정
                  </button>
                  <button className="pw-btn pw-btn--ghost"
                          onClick={() => del(it)} disabled={busy}
                          style={{ padding: '4px 8px', color: 'var(--pw-danger)' }}
                          aria-label="삭제">
                    <Trash2 size={14} aria-hidden="true" />
                  </button>
                </Td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><Td colSpan={6} style={{ textAlign: 'center', padding: '2rem',
                    color: 'var(--pw-text-muted)' }}>
                메뉴가 없습니다. 사진을 업로드하거나 수동 추가하세요.
              </Td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Draft 모달 (인라인 카드) */}
      {draft && (
        <DraftCard
          draft={draft}
          onChange={setDraft}
          onSave={saveDraft}
          onClose={() => setDraft(null)}
          busy={busy}
        />
      )}
      {confirmModalEl}
    </div>
  );
}

function Th({ children }) {
  return <th style={{ padding: '0.75rem 0.85rem', textAlign: 'left',
                      fontWeight: 600, color: 'var(--pw-text-secondary)' }}>{children}</th>;
}
function Td({ children, ...rest }) {
  return <td style={{ padding: '0.75rem 0.85rem' }} {...rest}>{children}</td>;
}
function Badge({ color, children }) {
  return <span style={{ display: 'inline-block', padding: '2px 8px',
                        borderRadius: 999, fontSize: 'var(--pw-fs-xs)',
                        border: `1px solid ${color}`, color }}>
    {children}
  </span>;
}

function DraftCard({ draft, onChange, onSave, onClose, busy }) {
  // 2026-05-27: PwModal 공용 컴포넌트로 재작성 (디자인 가이드 통일).
  return (
    <PwModal
      open={!!draft}
      onClose={onClose}
      busy={busy}
      title={draft.id ? '메뉴 수정' : '메뉴 추가'}
      size="md"
      footer={
        <>
          <button className="pw-btn pw-btn--ghost" onClick={onClose} disabled={busy}>
            취소
          </button>
          <button
            className="pw-btn"
            onClick={onSave}
            disabled={busy || !(draft.name || '').trim()}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <Save size={14} aria-hidden="true" />
            {busy ? '저장 중...' : (draft.id ? '저장' : '추가')}
          </button>
        </>
      }
    >
      <PwField label="이름 *">
        <input
          value={draft.name}
          onChange={(e) => onChange({ ...draft, name: e.target.value })}
          placeholder="예: 아메리카노"
          disabled={busy}
          autoFocus
        />
      </PwField>
      <PwField label="가격 (KRW)">
        <input
          value={draft.price}
          onChange={(e) => onChange({ ...draft, price: e.target.value })}
          placeholder="예: 4500 또는 4,500원"
          disabled={busy}
        />
      </PwField>
      <PwField label="설명 (선택)">
        <textarea
          rows={2}
          value={draft.description}
          onChange={(e) => onChange({ ...draft, description: e.target.value })}
          placeholder="예: 깊은 향의 에스프레소"
          disabled={busy}
        />
      </PwField>
      <PwField label="정렬 순서">
        <input
          type="number"
          value={draft.sort_order}
          onChange={(e) => onChange({ ...draft, sort_order: e.target.value })}
          disabled={busy}
        />
      </PwField>
    </PwModal>
  );
}
